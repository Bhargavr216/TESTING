# Chatbot Logic Updates - May 16, 2026

## Summary
Updated the chatbot question-answering logic in `src/naukri_bot.py` to handle specific user requirements for experience, location, F2F, and unknown questions.

## Changes Made

### 1. Experience Questions (Radio Buttons)
**Location**: `src/naukri_bot.py` line ~1843

**Change**: Updated radio question handler to always use 5 years for experience questions
```python
# Always use 5 years for experience questions (user requirement)
desired_years = 5.0
```

**Behavior**:
- For exact match questions: Answers "5"
- For range questions (e.g., "2-5 years", "4-9 years"): Automatically selects the range containing 5
- The `_pick_experience_radio_option` method already has logic to prefer ranges containing the desired value

### 2. Experience Questions (Text Input)
**Location**: `src/naukri_bot.py` line ~1700

**Already Implemented**: Text questions about experience answer "5"
```python
if not answer and (("experience" in question_lower) or _has_exp_token(question_lower) or ("idea" in question_lower)):
    answer = "5"
```

### 3. Location Questions
**Location**: `src/naukri_bot.py` line ~1705

**Already Implemented**: Location questions prefer "Hyderabad"
```python
if not answer and any(kw in question_lower for kw in ["location", "city", "where", "place"]):
    if any(kw in question_lower for kw in ["prefer", "preferred", "current", "present"]):
        answer = "Hyderabad"
    else:
        answer = "Hyderabad"
```

### 4. F2F / Walk-in Questions
**Location**: `src/naukri_bot.py` line ~1710

**Already Implemented**: F2F and walk-in questions answer "Yes"
```python
if not answer and any(kw in question_lower for kw in ["f2f", "face to face", "walk-in", "walk in", "walkin", "come to office", "visit office"]):
    answer = "Yes"
```

### 5. Previously Employed Questions
**Location**: `src/naukri_bot.py` line ~1715

**Already Implemented**: Previously employed questions answer "No"
```python
if not answer and any(kw in question_lower for kw in ["previously employed", "worked before", "prior employment", "past employment"]):
    answer = "No"
```

### 6. Unknown Questions (Skip Button)
**Location**: `src/naukri_bot.py` line ~1900

**Already Implemented**: Radio questions with no match try to click skip button
```python
if target_idx == -1:
    if await self._click_chat_skip_question_button():
        await human_delay(1, 2)
        log_info(f"Chat radio: skipped unknown question: '{question_text[:60]}'")
        return True
```

The `_click_chat_skip_question_button` method (line ~1380) tries multiple selectors:
- `button:has-text("Skip")`
- `a:has-text("Skip")`
- `div[role="button"]:has-text("Skip")`
- `span:has-text("Skip")`
- `li:has-text("Skip")`
- Regex: `/skip(\s+the)?\s+question/i`

## Testing Status

### Test Run: May 16, 2026 - 16:14
- **Command**: `auto --max-jobs 30 --no-headless`
- **Result**: Found 216 unique jobs, 66 after filtering
- **Issue**: All 66 jobs were "external apply" jobs (require application on company sites)
- **Outcome**: Chatbot logic was NOT tested because no jobs had direct "Apply" button on Naukri

### External Jobs Tracking
✅ Successfully tracked all 66 external jobs in `output/external_jobs.json`
✅ Generated HTML session report at `output/session_report_20260516_161639.html`

## Next Steps

To properly test the chatbot changes:
1. Wait for more jobs to be posted on Naukri that have direct "Apply" buttons
2. Run the automation again when fresh jobs are available
3. Monitor the logs for chatbot question handling
4. Verify that:
   - Experience questions answer "5" or select ranges containing 5
   - Location questions answer "Hyderabad"
   - F2F questions answer "Yes"
   - Previously employed questions answer "No"
   - Unknown questions click "Skip" button

## Files Modified
- `src/naukri_bot.py` (line ~1843): Updated radio question handler for experience

## Files Already Correct
- `src/naukri_bot.py` (lines ~1700-1720): Text question handlers
- `src/naukri_bot.py` (line ~1900): Skip button logic
- `src/naukri_bot.py` (line ~1380): Skip button click method
- `config/profile.yaml`: Comprehensive chatbot_custom_answers already configured

## Configuration
The `config/profile.yaml` already has 71 custom chatbot answers configured for common questions including:
- Walk-in/F2F: "Yes"
- Location preferences: "Bangalore, Chennai, Hyderabad"
- Experience: "5"
- Notice period: "30"
- Salary: Current "8", Expected "14"
- Education, skills, and technical experience details

These custom answers work in conjunction with the code logic to provide comprehensive chatbot handling.
