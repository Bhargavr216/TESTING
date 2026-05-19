# Latest Updates - May 17, 2026

## Changes Made

### 1. ✅ Filter Jobs by Date (2 Weeks Maximum)
**Location**: `src/naukri_bot.py` lines ~4129-4160

**What Changed**:
- Jobs older than 14 days are now automatically skipped
- Parses "X days ago" and "X weeks ago" formats
- Skips jobs with 15+ days, 2+ weeks, or 30+ days

**Logic**:
```python
# Skip if older than 14 days
if "day" in posted:
    days = extract_number(posted)
    if days > 14:
        skip_job()

# Skip if 2+ weeks old
if "week" in posted:
    weeks = extract_number(posted)
    if weeks >= 2:
        skip_job()
```

### 2. ✅ Sort Search Results by Date (Newest First)
**Location**: `src/naukri_bot.py` lines ~3820-3825

**What Changed**:
- Added `?sort=date` parameter to search URLs
- Ensures newest jobs appear first in parallel search
- Faster than clicking sort dropdown on each tab

**Before**:
```python
search_url = f"{NAUKRI_BASE}/{keyword}-jobs-in-{location}"
```

**After**:
```python
search_url = f"{NAUKRI_BASE}/{keyword}-jobs-in-{location}?sort=date"
```

### 3. ✅ Show "Posted" Date in External Jobs Report
**Location**: `src/naukri_bot.py` lines ~1067-1076, ~4640-4670

**What Changed**:
- External jobs now store the "posted" field (e.g., "2 days ago", "1 week ago")
- HTML report shows "Posted" column with this information
- JSON file also includes the posted date

**External Jobs JSON**:
```json
{
  "title": "QA Automation Engineer",
  "company": "Pice App",
  "url": "https://...",
  "location": "Bengaluru",
  "salary": "Not Disclosed",
  "posted": "2 days ago",  // NEW!
  "date": "2026-05-17 10:30:00"
}
```

**HTML Report**:
```
| # | Company | Job Title | Location | Posted | Salary | Link |
|---|---------|-----------|----------|--------|--------|------|
| 1 | Pice    | QA Auto   | Bangalore| 2 days ago | 12L | Open |
```

### 4. ✅ Exact Count Verification
**Location**: `src/naukri_bot.py` lines ~4024-4065

**Already Correct** - No changes needed:
- Loop continues until `successful_count >= max_jobs`
- External jobs return `status = "external_apply"` (NOT counted)
- Only `status = "applied"` increments the counter
- Warns if runs out of jobs before reaching target

## Testing

### Test Command:
```bash
".venv\Scripts\python.exe" -m src.main auto --max-jobs 30 --no-headless
```

### Expected Behavior:

1. **Search**: Opens 32 tabs with `?sort=date` parameter
2. **Filter**: Skips jobs older than 14 days
3. **Apply**: Continues until 30 successful applications
4. **External Jobs**: Stored with "posted" date in JSON and HTML
5. **Report**: Shows "Posted" column with dates

### Example Output:

```
>> Starting search for 8 roles across 4 locations...
INFO Opening 32 tabs for PARALLEL search...
INFO Executing parallel searches...
INFO   QA Automation Engineer in Bangalore: 45 jobs
INFO   SDET in Hyderabad: 38 jobs
...
OK Parallel search complete! Found 180 total jobs
INFO Jobs after filtering (strict): 85
INFO Filtered out 12 jobs older than 2 weeks

>> Applying to: Company A - QA Engineer
OK Applied successfully (1/30)

>> Applying to: Company B - SDET
INFO Skipping (external apply) - stored in external_jobs.json

>> Applying to: Company C - Automation Engineer
OK Applied successfully (2/30)

...continues until 30 successful applications...

OK Session complete. Successfully applied to 30/30 jobs
OK Saved 25 external jobs to output/external_jobs.json
OK Session report saved to output/session_report_20260517_103045.html
```

## Files Modified

1. **`src/naukri_bot.py`**:
   - Line ~1067: Added `"posted"` field to external jobs storage
   - Line ~3820: Added `?sort=date` to search URLs
   - Line ~3830: Updated pagination to maintain sort parameter
   - Line ~4129: Enhanced 2-week filter with day/week parsing
   - Line ~4640: Added "Posted" column to HTML report

## Configuration

### Change Maximum Job Age

Edit `src/naukri_bot.py` line ~4145:
```python
if days > 14:  # Change 14 to any number of days
    continue
```

Or for weeks:
```python
if weeks >= 2:  # Change 2 to any number of weeks
    continue
```

### Disable Date Filtering

Set `relaxed=True` in the filter call, or comment out the date filter section.

### Change Application Count

Edit `daily_auto.bat` line 23:
```bat
".venv\Scripts\python.exe" -m src.main auto --max-jobs 30 --no-headless
```

## Summary

✅ **Exact Count**: Bot applies to exactly N jobs (excluding external)
✅ **Date Sorted**: Search results sorted by newest first
✅ **2-Week Filter**: Jobs older than 14 days are skipped
✅ **Posted Date**: External jobs report shows when jobs were posted

All changes are complete and ready for testing!
