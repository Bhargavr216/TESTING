#!/bin/bash
# Naukri Auto Profile Update - Daily cron job
# Runs at 10:00 AM IST to update Naukri profile via resume upload
#
# Setup:
#   1. Export NAUKRI_EMAIL and NAUKRI_PASSWORD in your shell profile
#   2. Update the PROJECT_DIR variable below
#   3. Add to crontab: 0 10 * * * /path/to/update_profile_cron.sh

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

PROJECT_DIR="$HOME/Downloads/naukri_job_automation"

cd "$PROJECT_DIR" || exit 1
source .venv/bin/activate

naukri-auto update-profile >> "$PROJECT_DIR/data/cron.log" 2>&1
