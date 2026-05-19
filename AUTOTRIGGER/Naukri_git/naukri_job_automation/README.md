# Naukri Job Automation

CLI-based Naukri automation for scanning jobs, evaluating fit, auto-applying, tracking applications, refreshing your profile, generating ATS-friendly PDFs, and viewing saved reports in a local dashboard.

## What This Project Does

- Scans Naukri job listings using your target roles, locations, and filters
- Scores jobs against your profile and saves markdown reports for strong matches
- Applies to Easy Apply style jobs and auto-fills common screening questions
- Tracks application attempts in local TSV files to avoid duplicates
- Reuses a saved Playwright session in `auth.json` when available
- Generates HTML and PDF resumes from `cv.md`
- Starts a local reports dashboard to browse saved reports

## Tech Stack

- Python CLI with `click`
- Browser automation with Playwright
- Local web dashboard with FastAPI + Uvicorn
- YAML profile configuration
- Markdown-based CV input and report output

## Main Files

```text
naukri_job_automation/
|-- config/
|   |-- profile.example.yaml
|   `-- profile.yaml                  # created by setup, contains your personal config
|-- scripts/
|   `-- update_profile_cron.sh
|-- src/
|   |-- main.py                       # CLI entry point
|   |-- naukri_bot.py                 # login, apply, profile update, applied jobs
|   |-- scanner.py                    # scan Naukri search results
|   |-- evaluator.py                  # score and rank jobs
|   |-- tracker.py                    # applications.tsv helper
|   |-- pdf_generator.py              # cv.md -> HTML/PDF
|   |-- profile.py                    # config + env var loading
|   |-- reports_catalog.py            # reports data model for dashboard
|   |-- reports_ui_app.py             # FastAPI dashboard app
|   `-- templates/
|       `-- reports_dashboard.html
|-- templates/
|   `-- cv_template.html
|-- cv.example.md
|-- cv.md                             # your actual CV, local only
|-- requirements.txt
|-- setup.py
`-- README.md
```

## Prerequisites

- Python 3.10 or newer
- Google Chrome installed for best Playwright compatibility
- Internet access and a valid Naukri account
- Optional but recommended: Node.js, because `doctor` checks for it in the current implementation

## Install

### Option 1: Recommended install

This installs the package plus the `naukri-auto` command from `setup.py`.

```powershell
git clone https://github.com/Abhishek214/naukri_job_automation.git
cd naukri_job_automation

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
python -m playwright install chromium
```

### Option 2: Run directly from source

Use this if you do not want to install the CLI entry point globally into the virtual environment.

```powershell
git clone https://github.com/Abhishek214/naukri_job_automation.git
cd naukri_job_automation

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install fastapi "uvicorn[standard]"
python -m playwright install chromium
```

If you use Option 2, run commands as:

```powershell
python -m src.main --help
python -m src.main setup
```

## First-Time Setup

### 1. Create starter files

```powershell
naukri-auto setup
```

This creates:

- `config/profile.yaml` from `config/profile.example.yaml`
- `cv.md` if it does not already exist
- `data/`, `reports/`, and `output/`

### 2. Update `config/profile.yaml`

Important fields to review:

- `candidate.full_name`
- `candidate.email`
- `candidate.phone`
- `resume_path`
- `naukri_credentials.email`
- `naukri_credentials.password`
- `target_roles.primary`
- `target_roles.keywords_positive`
- `location.preferred_cities`
- `screening_answers.*`
- `search_preferences.max_applications_per_day`

The example profile is already structured for a QA/SDET-style job hunt, so customize it to your own role and skills before using `scan` or `apply`.

### 3. Update `cv.md`

Edit `cv.md` using the same section style shown in `cv.example.md`:

- `Summary`
- `Experience`
- `Skills`
- `Projects`
- `Education`
- `Certifications` if needed

### 4. Set environment variables

Environment variables override credentials in YAML and are safer than storing passwords in the config file.

PowerShell:

```powershell
$env:NAUKRI_EMAIL="your.naukri@email.com"
$env:NAUKRI_PASSWORD="your_password"
```

Bash:

```bash
export NAUKRI_EMAIL="your.naukri@email.com"
export NAUKRI_PASSWORD="your_password"
```

Optional session file override:

```powershell
$env:NAUKRI_STORAGE_STATE="C:\path\to\auth.json"
```

If `NAUKRI_STORAGE_STATE` is not set, the project uses `auth.json` in the repo root.

### 5. Verify everything

```powershell
naukri-auto doctor
```

## How To Run

After installing with `pip install -e .`, use:

```powershell
naukri-auto --help
```

If you chose source-only usage, use:

```powershell
python -m src.main --help
```

## All Commands

### `setup`

Creates initial local files and directories.

```powershell
naukri-auto setup
```

### `doctor`

Checks runtime dependencies and basic project setup.

```powershell
naukri-auto doctor
```

### `scan`

Scans job listings on Naukri and evaluates them.

```powershell
naukri-auto scan
naukri-auto scan -k "python developer" -k "backend engineer" -l "Bangalore"
naukri-auto scan --fresh --pages 5
```

Useful options:

- `-k`, `--keywords`
- `-l`, `--location`
- `-p`, `--pages`
- `--fresh`

### `apply`

Scans and applies to jobs automatically using browser automation.

```powershell
naukri-auto apply
naukri-auto apply --dry-run
naukri-auto apply -k "sdet" -l "Remote" --max-jobs 10
naukri-auto apply --headless
```

Useful options:

- `-k`, `--keywords`
- `-l`, `--location`
- `-m`, `--max-jobs`
- `--dry-run`
- `--headless` or `--no-headless`

## Local AI (Optional)

You can optionally use a **local LLM** to answer unknown screening chatbot questions (radio/text/checkbox),
based on your `config/profile.yaml`.

Recommended setup (Ollama):

```powershell
# Install Ollama (Windows) from the official installer, then:
ollama pull llama3.1:8b
ollama serve
```

Enable in `config/profile.yaml`:

```yaml
local_ai:
  enabled: true
  mode: "fallback"   # or "always"
  provider: "ollama"
  base_url: "http://127.0.0.1:11434"
  model: "llama3.1:8b"
```

Notes:
- The bot never sends your Naukri password to the model (or anywhere).
- Local AI is used as a fallback when built-in rules can’t confidently answer.

### Custom (Hard) Answers

If you want fixed answers for specific questions, add `chatbot_custom_answers` in `config/profile.yaml`:

```yaml
chatbot_custom_answers:
  - kind: "radio"
    match_type: "contains"
    match: "family member"
    answer: "No"
  - kind: "text"
    match_type: "contains"
    match: "college"
    answer: "GIST"
```

### `apply-url`

Applies to one specific Naukri job URL.

```powershell
naukri-auto apply-url "https://www.naukri.com/job-listings-..."
```

Useful options:

- `--headless` or `--no-headless`

### `tracker`

Shows summary and recent application history from `data/applications.tsv`.

```powershell
naukri-auto tracker
naukri-auto tracker --limit 20
```

Useful options:

- `-n`, `--limit`

### `evaluate`

Reads `data/scan-history.tsv`, evaluates saved jobs, and writes high-scoring reports.

```powershell
naukri-auto evaluate
```

### `pdf`

Generates an ATS-friendly resume in `output/`.

```powershell
naukri-auto pdf
naukri-auto pdf --job-url "https://www.naukri.com/job-listings-..."
naukri-auto pdf --output "cv-target-company"
```

Useful options:

- `--job-url`
- `-o`, `--output`

### `update-profile`

Logs into Naukri and refreshes your profile.

```powershell
naukri-auto update-profile
naukri-auto update-profile --headless
```

Useful options:

- `--headless` or `--no-headless`

### `applied`

Fetches jobs already applied to on Naukri and prints them in a table.

```powershell
naukri-auto applied
```

Useful options:

- `--headless` or `--no-headless`

### `reports-ui`

Starts a local dashboard for the `reports/` folder.

```powershell
naukri-auto reports-ui
naukri-auto reports-ui --host 127.0.0.1 --port 8765
naukri-auto reports-ui --reports-dir reports --no-browser
```

Open the shown URL in your browser, usually:

```text
http://127.0.0.1:8765
```

Important:

- Do not open `src/templates/reports_dashboard.html` directly as a file
- Start the dashboard through `naukri-auto reports-ui` so the API routes work

Useful options:

- `--host`
- `--port`
- `--reports-dir`
- `--no-browser`

## Recommended Workflow

```powershell
naukri-auto setup
naukri-auto doctor
naukri-auto scan
naukri-auto apply --dry-run
naukri-auto apply --max-jobs 5
naukri-auto tracker
naukri-auto reports-ui
```

## Output Files

The project writes local data into these paths:

- `config/profile.yaml`: your personal profile and preferences
- `cv.md`: your source CV in Markdown
- `auth.json`: saved Playwright login session
- `data/applications.tsv`: application tracker
- `data/scan-history.tsv`: scanned jobs history
- `reports/*.md`: job evaluation reports
- `reports/applied/*.md`: applied jobs reports
- `output/*.html`: intermediate resume HTML
- `output/*.pdf`: generated resume PDFs

## Notes On Behavior

- The browser is visible by default because Naukri can be harder to automate in headless mode
- If Chrome is not available, the code falls back to Playwright Chromium
- Login may still require manual CAPTCHA, OTP, or human intervention
- Session reuse is supported through `auth.json`
- Duplicate applications are reduced using local tracker files and job IDs

## Scheduling

The repo includes `scripts/update_profile_cron.sh` for Unix-like systems.

Example cron entry:

```bash
0 10 * * * /path/to/naukri_job_automation/scripts/update_profile_cron.sh
```

Before using it:

- update `PROJECT_DIR` inside the script
- ensure the virtual environment exists
- export `NAUKRI_EMAIL` and `NAUKRI_PASSWORD`

For Windows, use Task Scheduler with a command that activates the virtual environment and runs:

```powershell
naukri-auto update-profile
```

This repo also includes `daily_auto.bat` (update profile + early access share-interest + apply) and `daily_auto_hidden.vbs` (runs the batch file without a visible console window). `daily_auto.bat` writes logs under `logs/` so you can debug Startup/Task Scheduler runs.

Windows helpers:

- `install_daily_task.bat`: creates a Scheduled Task (`NaukriDailyAuto`) that runs at logon + daily (default 10:00) and uses a once-per-day guard.
- `install_startup_launcher.bat`: adds a Startup-folder launcher (`NaukriStartupLauncher.bat`) that calls into this repo.

Important: don’t *copy* `daily_auto.bat` into the Startup folder (it will look for `.venv` in Startup). Keep `daily_auto.bat` in the repo and use the installer scripts above.

## Security

- Never commit `config/profile.yaml`, `cv.md`, `auth.json`, or generated reports containing personal data
- Prefer `NAUKRI_EMAIL` and `NAUKRI_PASSWORD` over hardcoding credentials
- Review every profile field before enabling automatic application flows
- Keep `--no-headless` as the safer default if you want to monitor the browser

## Troubleshooting

### `naukri-auto` command not found

Install the package into the active virtual environment:

```powershell
python -m pip install -e .
```

### Playwright browser missing

```powershell
python -m playwright install chromium
```

### Reports UI fails to start

Install the missing web dependencies:

```powershell
python -m pip install fastapi "uvicorn[standard]"
```

### Login keeps failing

- verify `NAUKRI_EMAIL` and `NAUKRI_PASSWORD`
- check if Naukri is showing CAPTCHA or OTP
- delete or refresh `auth.json` if the saved session is stale
- try visible browser mode with `--no-headless`

## License

MIT
