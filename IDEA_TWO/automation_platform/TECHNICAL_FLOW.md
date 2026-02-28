# 🏗️ Framework Technical Flow Documentation

This document explains exactly how the framework works, from the moment you start it to the moment the final report is generated. It's written for everyone—even if you've never seen the code before!

---

## 1. 📂 Core File Explanations

### **`suite.json`**
The "Global Controller". This file tells the engine which services to validate (FSM, MFS, FOS) and what types of tests to run (Happy Path, Retry, etc.). It also defines where the scenarios are located.

### **`setup_db.py`**
The "Data Architect". This script creates the entire world for the framework.
- It connects to your PostgreSQL database.
- It creates 3 separate databases: `fsm_db`, `mfs_db`, and `fos_db`.
- It defines the table schemas (columns like `event_id`, `operation`, `exception`).
- It seeds "mock data" so we have something to validate.

### **`engine/runner.py`**
The "Project Manager". When you run this, it:
1.  Loads the `suite.json`.
2.  Discovers all the scenario files in the `scenarios/` folders.
3.  Initializes the `ReportBuilder`.
4.  Loops through each scenario and hands it to the `StateExecutor`.

### **`engine/state_executor.py`**
The "Engine Driver". This is the heart of the flow.
1.  **Trigger Event**: It reads the `event_payload` and `look_up_ref` from the scenario.
2.  **Resolve Lookups**: It extracts IDs (like `event_id`) from the payload.
3.  **Execute Rules**: It looks at each rule in the scenario (like `smart_validate` or `audit_validate`) and calls the correct validator.

### **`engine/validators/` (The Specialists)**
- [**`audit_rule.py`**](file:///c:/Users/bharg/Desktop/TMP/WORK/AUTOMATION_IDEA_01/IDEA_TWO/automation_platform/engine/validators/audit_rule.py): Specialized in sequence and retry validation. It checks if steps happened in the right order (e.g., 1. Create, 2. Validate, 3. Published).
- [**`smart_rule.py`**](file:///c:/Users/bharg/Desktop/TMP/WORK/AUTOMATION_IDEA_01/IDEA_TWO/automation_platform/engine/validators/smart_rule.py): The most powerful rule. It can check multiple tables and even deep JSON attributes (like `order.item_name`) in one go.

### **`engine/report_builder.py`**
The "Artist". It takes all the Pass/Fail results and builds the beautiful HTML dashboard you see in your browser.

---

## 2. 🌊 Step-by-Step Execution Flow

### **Phase 1: Preparation**
1.  You run `python setup_db.py`.
2.  The script creates the tables and seeds data (e.g., a Happy Path for FSM).
3.  Scenario files are generated on disk in the `scenarios/` folder.

### **Phase 2: Discovery**
1.  You run `python -m engine.runner`.
2.  The engine looks at `suite.json` and finds all services listed.
3.  It scans `scenarios/fsm/*.json`, `scenarios/mfs/*.json`, etc.

### **Phase 3: Execution (Inside a single Scenario)**
1.  The `StateExecutor` reads the scenario's `event_payload`.
2.  It extracts the `event_id` (e.g., `fsm_001`).
3.  It calls the `AuditRule` validator.
4.  The `AuditRule` runs a SQL query: `SELECT * FROM fsm_audit WHERE event_id = 'fsm_001'`.
5.  It compares the actual rows from the database with the expected sequence in the JSON.
6.  If everything matches, it returns a **PASS**.

### **Phase 4: Reporting**
1.  The `Runner` collects all results.
2.  The `ReportBuilder` generates `reports/report.html`.
3.  You open the report and see the success!

---

## 3. 🔍 Line-by-Line Breakdown: `AuditRule` Logic
Let's look at a critical part of the validation logic in [audit_rule.py](file:///c:/Users/bharg/Desktop/TMP/WORK/AUTOMATION_IDEA_01/IDEA_TWO/automation_platform/engine/validators/audit_rule.py):

- **Line 33**: `ORDER BY event_time ASC` - This ensures we validate the sequence in the exact order it happened.
- **Line 57**: `retry_found = len(...)` - This dynamically counts how many times the system retried by looking for "VALIDATE" operations with exceptions.
- **Line 92**: `exc_match = act_exc == exp_exc` - This checks if the exception message matches exactly (or is NULL).

---

## 4. 🚀 Why use this Framework?
1.  **No Coding for Tests**: You only write JSON files.
2.  **Scalable**: Adding a new service is as easy as adding a new database config.
3.  **Audit-Ready**: The report provides a full audit trail of exactly what was checked and why it passed or failed.
