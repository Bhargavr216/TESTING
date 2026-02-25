# Idea 1 - Database Validation Automation

This project validates whether event processing persisted the correct records in PostgreSQL, table by table, column by column, with both positive and negative test scenarios.

It compares:
- **Actual DB rows** fetched by lookup keys (for example `order_id`)
- **Expected rows** stored in JSON files
- **Rules** defined per table in a schema JSON

It produces:
- Rich terminal output (pass/fail/skip)
- An interactive HTML report with test-case collapsible sections, sidebar navigation, and expand/collapse controls

## What This Framework Covers

- Table persistence checks (`PERSIST`, `NOT_PERSIST`)
- Mandatory-table enforcement for `expected_tables`
- Row matching using `primary_lookup` and optional `secondary_lookup`
- Generated column presence checks (for example `audit_id` must not be `NULL`)
- Unique constraint validation at runtime
- JSON column validation:
  - required nested paths
  - ignored paths
  - deep value comparison
- Semantic rule validation:
  - `nullable_presence`
- Retry expectation validation (operation count per lookup, e.g., `VALIDATE` must appear 3 times)

## Project Structure

```text
AUTOMATION_IDEA_01/
├─ README.md
├─ .gitignore
└─ idea1_project/
   ├─ runner.py
   ├─ config/
   │  └─ db_config.example.json
   ├─ payloads/
   │  └─ event_payloads.json
   ├─ schemas/
   │  └─ table_schema.json
   ├─ expected/
   │  └─ tables/
   │     ├─ orders.json
   │     ├─ fulfilment.json
   │     ├─ operations.json
   │     ├─ audit_logs.json
   │     └─ job_queue.json
   ├─ logs/
   └─ reports/
```

## Prerequisites

- Python 3.10+
- PostgreSQL accessible from your machine
- Python packages:
  - `psycopg2`
  - `jsonschema`

Install dependencies:

```powershell
cd idea1_project
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install psycopg2-binary jsonschema
```

## Configuration

Create local DB config from sample:

```powershell
copy .\config\db_config.example.json .\config\db_config.json
```

Edit `idea1_project/config/db_config.json` with your actual DB credentials.

> Note: `db_config.json` is git-ignored to avoid committing secrets.

## How to Run

```powershell
cd idea1_project
.\venv\Scripts\Activate.ps1
python runner.py
```

Outputs:
- Console execution summary
- HTML report at `idea1_project/reports/idea1_report.html`

## Database Bootstrap Script

A full DB setup script is included:

- `idea1_project/db/setup_database.sql`

It will:
- create database `idea1_testing` if missing
- create all required tables
- seed sample rows for `ORD123`, `ORD124`, and `ORD500`

Run from PowerShell:

```powershell
$env:PGPASSWORD="<your_password>"
psql -h localhost -p 5432 -U postgres -d postgres -f idea1_project/db/setup_database.sql
```

## Scenarios in Payloads

`payloads/event_payloads.json` defines test cases.

Each case typically contains:
- `test_case_id`
- `scenario_name`
- `event_type`
- `lookup_ids` (for example `order_id`)
- `expected_tables`
- `table_expectations`
- optional `retry_expectations`

### Retry Example

```json
"retry_expectations": {
  "audit_logs": [
    { "operation": "VALIDATE", "count": 3 }
  ]
}
```

This means for the same lookup id, `audit_logs` must contain operation `VALIDATE` exactly 3 times.

## Schema Rules

`schemas/table_schema.json` controls validation behavior per table:

- `primary_lookup`: required
- `secondary_lookup`: optional
- `mandatory_columns`: required columns to verify
- `json_columns`: JSON field rules (`required`, `ignored`)
- `semantic_rules`: semantic checks (`nullable_presence`)
- `generated_columns`: columns expected to be auto-populated
- `unique_constraints`: runtime duplicate detection

## Expected Data Files

Expected rows live in:

- `expected/tables/orders.json`
- `expected/tables/fulfilment.json`
- `expected/tables/operations.json`
- `expected/tables/audit_logs.json`
- `expected/tables/job_queue.json`

Best practices:
- Keep expected rows aligned with table schema
- Ensure lookup keys exist in expected rows
- Include JSON structure required by schema rules

## HTML Report Features

- Sticky top bar
- `Expand All` / `Collapse All`
- Left sidebar with testcase links
- Collapsible testcase cards
- Per-case result chips (pass/fail/skip counts)
- Table-level failure blocks showing expected vs actual details

## Common Failure Causes

1. Missing mandatory rows for `expected_tables`
2. Mismatch in operation/lookup key used for matching
3. Missing generated values (e.g., `audit_id` is NULL)
4. JSON required paths absent in actual or expected
5. Retry operation count mismatch

## Typical DB Debug Queries

```sql
SELECT * FROM audit_logs WHERE order_id IN ('ORD124','ORD500');
SELECT * FROM job_queue  WHERE order_id IN ('ORD124','ORD500');
```

## Notes

- This framework is schema-driven and easy to extend by editing payloads + expected files + schema rules.
- If you add new semantic rule types in schema, update `runner.py` to enforce them.

## Future Enhancements

- Distinct failure categories in summary (actual vs expected)
- Deduplicated failure summary
- Optional strict mode (row-for-row exact matching)
- CI pipeline integration and artifact upload for HTML reports
