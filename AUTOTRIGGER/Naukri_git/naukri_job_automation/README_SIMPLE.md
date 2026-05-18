# Naukri Job Automation - Simplified

Automated job application tool for Naukri.com with parallel search and smart chatbot handling.

## Features

✅ **Profile Update** - Automatically updates your Naukri resume  
✅ **Early Access Roles** - Applies to early access opportunities  
✅ **Smart Job Application** - Parallel search + Auto-apply with chatbot handling  
✅ **Daily Auto Run** - One command to do everything  

## Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure your profile
# Edit config/profile.yaml with your details
```

### 2. Commands

#### Daily Auto Run (Recommended)
```bash
# Windows
daily_auto.bat

# Or manually
python -m src.main auto --max-jobs 50 --no-headless
```

This will:
1. Update your Naukri profile resume
2. Apply to early access roles
3. Search and apply to 50 jobs (successful applications, not attempts)

#### Individual Commands

**Update Profile Only:**
```bash
python -m src.main update-profile --no-headless
```

**Apply to Jobs Only:**
```bash
python -m src.main apply --max-jobs 50 --no-headless
```

## Configuration

Edit `config/profile.yaml`:

```yaml
# Your credentials
naukri_credentials:
  email: "your@email.com"
  password: "yourpassword"

# Resume file
resume_path: "config/Resume.pdf"

# Target roles (will search in parallel)
target_roles:
  primary:
    - "QA Automation Engineer"
    - "SDET"
    - "Automation Engineer"

# Search settings
search_preferences:
  apply_delay_seconds: 3  # Delay between applications
  max_applications_per_day: 50
```

## How It Works

### Parallel Search (Fast!)
- Opens 16 browser tabs simultaneously
- Searches all role+location combinations at once
- Collects 100+ jobs in seconds instead of minutes

### Smart Application
- Continues until target successful applications reached
- Skips external applications automatically
- Handles chatbot questions with 71+ pre-configured answers
- Retries failed applications

### Chatbot Handling
71 pre-configured answers for common questions:
- Experience years
- Skills (Java, Selenium, API Testing, etc.)
- Salary expectations
- Notice period
- Location preferences
- Work flexibility (shifts, remote, etc.)

## Startup Integration

### Windows Startup
1. Press `Win + R`
2. Type `shell:startup` and press Enter
3. Create shortcut to `daily_auto.bat`
4. Done! Will run on every startup

## Performance

- **Parallel Search**: 16 tabs simultaneously
- **Speed**: 3-4x faster than sequential
- **Time**: ~15-20 minutes for 50 applications
- **Success Rate**: Skips unsuitable jobs, continues until target reached

## Files Structure

```
├── config/
│   ├── profile.yaml          # Your configuration
│   └── Resume.pdf            # Your resume
├── data/
│   └── applications.tsv      # Application tracking
├── reports/
│   └── applied/              # Application reports
├── src/
│   ├── main.py              # CLI commands
│   ├── naukri_bot.py        # Core automation
│   └── ...
├── daily_auto.bat           # Daily automation script
└── auth.json                # Session storage (auto-created)
```

## Troubleshooting

**Login fails:**
- Check credentials in `config/profile.yaml`
- Delete `auth.json` and try again

**Browser closes unexpectedly:**
- Use `--no-headless` flag (visible browser)
- Naukri blocks headless browsers

**Not finding jobs:**
- Check `target_roles` in config
- Verify location preferences
- Try broader keywords

## Support

For issues or questions, check the logs in the console output.
