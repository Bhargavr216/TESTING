# Windows Startup Setup Guide

## What Happens on Startup

When your computer starts, the automation will automatically:
1. ✅ **Update Profile** - Upload latest resume to Naukri
2. ✅ **Early Access** - Click "Share Interest" on early access roles
3. ✅ **Apply to Jobs** - Apply to 50 jobs (exact count, not including external)
4. ✅ **Generate Report** - Create HTML report with results and external jobs

## Files Involved

### Main Files (Already in your project):
1. **`daily_auto_hidden.vbs`** - Runs the automation silently (no window)
2. **`daily_auto.bat`** - The actual automation script
3. **`startup_launcher.bat`** - Launcher that runs on Windows startup

### What Each File Does:

```
Windows Startup
    ↓
startup_launcher.bat (in Startup folder)
    ↓
daily_auto_hidden.vbs (runs hidden)
    ↓
daily_auto.bat (runs Python automation)
    ↓
Python: Update → Early Access → Apply 50 jobs → Report
```

## Installation Steps

### Option 1: Automatic Installation (RECOMMENDED)

Run this command in your project folder:
```bash
install_startup_launcher.bat
```

This will:
- Copy `startup_launcher.bat` to your Windows Startup folder
- Set environment variable `NAUKRI_AUTOMATION_HOME`
- Configure everything automatically

**After running, restart your computer or sign out/in for changes to take effect.**

### Option 2: Manual Installation

1. **Open Startup Folder**:
   - Press `Win + R`
   - Type: `shell:startup`
   - Press Enter

2. **Copy the launcher**:
   - Copy `startup_launcher.bat` from your project folder
   - Paste it into the Startup folder

3. **Set environment variable**:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "User variables", click "New"
   - Variable name: `NAUKRI_AUTOMATION_HOME`
   - Variable value: `C:\Users\bharg\Desktop\TMP\WORK\Naukri_git\naukri_job_automation` (your project path)
   - Click OK

4. **Restart** your computer or sign out/in

## Verify Installation

After restart, check:
1. **Logs folder**: `logs/daily_auto_YYYYMMDD-HHMMSS.log`
2. **Output folder**: `output/session_report_YYYYMMDD_HHMMSS.html`
3. **External jobs**: `output/external_jobs.json`

## Configuration

### Change Number of Applications

Edit `daily_auto.bat` line 23:
```bat
".venv\Scripts\python.exe" -m src.main auto --max-jobs 50 --no-headless
```

Change `50` to any number you want (e.g., `30`, `100`)

### Run Visible (for debugging)

Edit `daily_auto.bat` line 23, remove `--no-headless`:
```bat
".venv\Scripts\python.exe" -m src.main auto --max-jobs 50
```

### Disable Startup

**Option 1**: Delete from Startup folder
- Press `Win + R` → `shell:startup`
- Delete `NaukriStartupLauncher.bat`

**Option 2**: Disable in Task Manager
- Press `Ctrl + Shift + Esc`
- Go to "Startup" tab
- Find "NaukriStartupLauncher"
- Right-click → Disable

## Troubleshooting

### Check if it's running:
```bash
# Look for recent log files
dir logs\daily_auto_*.log /o-d
```

### Check startup log:
```bash
type %TEMP%\naukri_startup_launcher.log
```

### Test manually:
```bash
# Run visible to see what happens
daily_auto.bat
```

### Common Issues:

1. **"NAUKRI_AUTOMATION_HOME is not set"**
   - Run `install_startup_launcher.bat` again
   - Restart computer or sign out/in

2. **"Virtual environment .venv not found"**
   - Make sure you're in the project folder
   - Run: `python -m venv .venv`
   - Run: `.venv\Scripts\pip install -r requirements.txt`

3. **Browser doesn't open**
   - Check if `--no-headless` flag is in `daily_auto.bat`
   - Naukri blocks headless browsers, so visible mode is required

4. **No applications (0/50)**
   - This is normal if all jobs are external apply jobs
   - Check `output/external_jobs.json` for stored external jobs
   - Try running at different times when more jobs are posted

## Alternative: Task Scheduler (More Reliable)

For better reliability, use Windows Task Scheduler instead:

```bash
install_daily_task.bat
```

This creates a scheduled task that runs daily at a specific time, which is more reliable than Startup folder.

## Summary

**File to place in Startup**: `startup_launcher.bat` (automatically done by `install_startup_launcher.bat`)

**What it does**:
1. Update profile (resume upload)
2. Early access (share interest)
3. Apply to N jobs (exact count, excluding external)
4. Generate HTML report with results

**Logs**: `logs/daily_auto_YYYYMMDD-HHMMSS.log`
**Reports**: `output/session_report_YYYYMMDD_HHMMSS.html`
**External Jobs**: `output/external_jobs.json`
