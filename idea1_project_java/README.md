# Idea 1 — Event-Driven Database Validation Automation (Java)

## End-to-End Explanation
The Maven runner reads scenario definitions from `payloads/event_payloads.json`, resolves lookup keys via the table schemas (`schemas/table_schema.json`), and compares persisted PostgreSQL rows to the expected dataset (`expected/tables/*.json`). Each `TestCase` in `src/` orchestrates the flow: query the database, apply semantic rules (nullable checks, generated-column guards, retry counts), log the result, and render the consolidated HTML report in `reports/idea1_report.html`.

## Key Components & Coverage
- **`src/main/java/`**: Java helpers that normalize lookups, compare JSON columns, and articulate semantic validators (nullable, JSON path, uniqueness).
- **`config/db_config.json`**: database credentials derived from the sample file.
- **`payloads/event_payloads.json`**: describes event types, expected tables, and retry expectations (e.g., `audit_logs` must contain `VALIDATE` three times).
- **`schemas/table_schema.json`**: manages `primary_lookup`, `mandatory_columns`, JSON rules, semantic rules, and generated-column expectations.
- **`expected/tables/`**: stores the canonical rows for `orders`, `fulfilment`, `operations`, `audit_logs`, and `job_queue`.
- **`db/setup_database.sql`**: bootstraps database objects and seeds sample data (`ORD123`, `ORD124`, `ORD500`).

## Setup & Execution
1. Install **Java 17+**, **Maven 3.6+**, and ensure PostgreSQL is accessible.
2. Copy `config/db_config.example.json` to `config/db_config.json` and populate credentials.
3. Run the SQL bootstrap script: `psql -h localhost -U postgres -d postgres -f db/setup_database.sql`.
4. Build the Maven project: `mvn clean package`.
5. Run the automation via `mvn exec:java -Dexec.mainClass="com.idea1.automation.runner.Runner"` or `java -jar target/automation-1.0-SNAPSHOT.jar`.

## Reporting & Observability
- Console logs report pass/fail statuses, lookup mismatches, and semantic rule IDs.
- The HTML report (`reports/idea1_report.html`) includes collapsible sections, pass/fail chips, tables detailing expected vs actual rows, and helpful timestamps.
- Failure logs include SQL queries executed and the comparison diffs for quick debugging.

## Important Interview Questions & Answers
1. **Q:** How do you keep validation rules decoupled from code?  
   **A:** Store them in `schemas/table_schema.json` (lookup columns, mandatory fields, JSON paths) so adding a new table only requires updating the schema file and expected data.
2. **Q:** What’s the best way to compare JSON columns across rows?  
   **A:** Use Jackson or Gson to parse the JSON and compare required vs ignored paths while normalizing order; the framework populates `schema`.`json_columns` to guide the comparison.
3. **Q:** How do you verify retry behavior in audit tables?  
   **A:** Each payload defines `retry_expectations`; the runner counts operations (e.g., `VALIDATE`) per lookup and asserts the count matches expectations before reporting.

## Theory Knowledge for Interviews
- **Schema-Driven Testing:** Validation rules live in config files describing lookups, mandatory columns, JSON validation, and semantic constraints — the code acts as a generic engine.
- **Positive vs Negative Flows:** The project illustrates both `PERSIST` and `NOT_PERSIST` scenarios, teaching how to assert presence and absence in DB tests.
- **Event-Driven Verification:** Understand how events trigger downstream persistence, how to extract keys from payloads, and how to correlate with row data for full traceability.

## Troubleshooting & Tips
- Adjust `config/db_config.json` to match your JDBC URL and driver (Postgres vs Azure SQL) before running.
- Use SQL queries from the logs (e.g., `SELECT * FROM audit_logs WHERE order_id = 'ORD124';`) to validate mismatched rows.
- Keep expected JSON aligned with schema versions to prevent false schema errors.

## Next Steps
- Wire the HTML report as a CI artifact and break down failures per table for quicker triage.
- Externalize retry rules and semantic checks into a shared library so the same engine can validate other services (FSM, MFS, FOS).
