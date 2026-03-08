# Idea 1 — Event-Driven Database Validation (Python)

## End-to-End Explanation
The Python runner (`runner.py`) reads JSON scenarios (`payloads/event_payloads.json`), triggers the associated event IDs, resolves lookup keys, and validates the persisted rows table by table. Each scenario carries metadata (`expected_tables`, `table_expectations`, `retry_expectations`) that the runner enforces by comparing actual PostgreSQL rows (`psycopg2` queries) against `expected/tables/*.json` plus JSON schema rules before emitting console logs and an interactive HTML report (`reports/idea1_report.html`).

## Key Components & Coverage
- **`config/db_config.json`**: database credentials configured from the sample file; the runner is designed to keep secrets out of source control.
- **`payloads/event_payloads.json`**: test cases describing order IDs, services (PERSIST vs NOT_PERSIST), and the tables to check.
- **`schemas/table_schema.json`**: rules for lookup columns, mandatory fields, semantic rules such as `nullable_presence`, and JSON column requirements.
- **`expected/tables/*.json`**: expected rows for `orders`, `fulfilment`, `operations`, `audit_logs`, and `job_queue`.
- **`logs/` & `reports/`**: capture detailed verification traces plus the collapsible HTML dashboard.
- **`db/setup_database.sql`**: seeds `idea1_testing` with sample data (e.g., `ORD123`, `ORD124`, `ORD500`) for repeatable testing.

## Setup & Execution
1. Install **Python 3.10+** and ensure PostgreSQL is reachable.
2. Create a virtual environment: `python -m venv venv` and activate it (`.\venv\Scripts\Activate.ps1` on Windows or `source venv/bin/activate` on Unix).
3. Install dependencies: `pip install -r requirements.txt` (contains `psycopg2-binary` and `jsonschema`).
4. Copy `config/db_config.example.json` to `config/db_config.json` and fill in the database connection string.
5. Run the DB bootstrap: `psql -h localhost -U postgres -d postgres -f db/setup_database.sql`.
6. Execute the validation: `python runner.py`. Review `reports/idea1_report.html` for collapsible test-case summaries, failure tables, and the sidebar navigation.

## Reporting & Observability
- Writes structured logs for each scenario (pass/fail/skip counts, actual vs expected differences).
- Outputs a navigable HTML report with expandable/collapsible cards per test case plus aggregated pass/fail badges.
- Supports rerun failure focus via `reports/idea1_report.html` and raw logs stored under `logs/`.

## Important Interview Questions & Answers
1. **Q:** How do you check data persistence across tables from a single event?  
   **A:** `payloads/event_payloads.json` defines the `expected_tables` for each event; the runner matches rows via `primary_lookup`/`secondary_lookup`, applies table-specific schemas, and compares each column to the JSON-defined expectations (`expected/tables/*.json`).
2. **Q:** Why is schema-driven validation useful in this project?  
   **A:** Schema rules (mandatory columns, JSON path checks, semantic rules such as `nullable_presence`) keep validation logic declarative, so adding new tables only requires updating `schemas/table_schema.json` and not the runner logic.
3. **Q:** How do you handle retries and audit validation?  
   **A:** The scenario payloads include `retry_expectations` that assert how many times operations like `VALIDATE` appear per lookup; the runner tallies actual rows and compares counts before reporting success/failure.

## Theory Knowledge for Interviews
- **Schema-Driven Testing:** Designing verification rules in JSON ensures the code stays generic while the configuration covers table/column-specific nuances.
- **Positive vs Negative Scenario Coverage:** The dataset contains both `PERSIST` (expected rows) and `NOT_PERSIST` entries, teaching how to assert absence just as strongly as presence.
- **Data Comparisons & JSON Diffing:** Leveraging `jsonschema` and custom comparators helps detect nested path mismatches, ignored paths, and generated-column violations (e.g., ensuring `audit_id` isn’t `NULL`).

## Troubleshooting & Tips
- If you see credential errors, re-check `config/db_config.json` for host, port, and SSL settings.
- Running `psql` queries (`SELECT * FROM audit_logs WHERE order_id = 'ORD124';`) helps debug mismatch reports.
- Keep expected JSON aligned to the schema version to avoid schema validation errors; `logs/*.log` will show schema rule IDs for failing rows.

## Next Steps
- Introduce CI gating to publish the HTML report as an artifact and fail builds on regression.
- Extend the runner to support SQL Server/PostgreSQL parity by isolating connector logic behind an adapter layer.
