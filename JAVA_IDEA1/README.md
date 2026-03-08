# Idea 1 — Azure Event Hub to Database Validation Automation (Java)

## End-to-End Explanation
The framework orchestrates Azure Event Hub payloads, waits for downstream processing, and validates persistence inside an SQL database. It reads dynamic payloads (`payloads/event_payloads.json`), publishes them to Event Hub (via `EventHubPublisher` helpers), waits for the service to process them, and then queries tables defined in `schemas/table_schema.json`. The sequence is: clear database state → publish payload → wait for Azure processing → validate `orders`, `audit_logs`, and related tables → report results via HTML/CSV artifacts.

## Key Components & Coverage
- **`config/db_config.json`**: connection strings for Azure SQL or PostgreSQL plus Event Hub details (`eventHubConnectionString`, `eventHubName`).
- **`payloads/event_payloads.json`**: supports single objects and arrays to validate both scalar and bulk event flows.
- **`schemas/` & `expected/`**: define lookup strategies, mandatory columns, JSON rules, and expected rows for each table.
- **`src/`**: Java logic that triggers Event Hub messages, polls the database, and formats results (reports live in `reports/idea1_report.html`).
- **`reports/`**: interactive HTML with summary cards plus deep-dives for each test case.
- **`create_pdf.py`** (optional): converts HTML reports into portable PDFs for stakeholder sharing.

## Setup & Execution
1. Install **Java 17+**, **Maven**, and ensure network access to Azure Event Hub/SQL.
2. Populate `config/db_config.json` with your Azure credentials (copy from `config/db_config.example.json`).
3. Build the project: `mvn clean package`.
4. Run the runner via Maven: `mvn exec:java -Dexec.mainClass="com.idea1.automation.runner.Runner"`.
5. Alternatively run the shaded JAR: `java -jar target/automation-1.0-SNAPSHOT.jar`.
6. After execution, open `reports/idea1_report.html` for scenario statuses and failure tables.

## Reporting & Observability
- HTML report includes collapsible cards, pass/fail chips, and expandable sections for each table comparison.
- Detailed logs capture Event Hub interactions, SQL queries executed, and JSON diffs.
- Optionally, `create_pdf.py` generates a PDF summary from the HTML report for offline sharing.

## Important Interview Questions & Answers
1. **Q:** How do you simulate Azure Event Hub workloads in a validation suite?  
   **A:** Payloads in `payloads/event_payloads.json` are published to Event Hub, and the runner polls Azure SQL to confirm the messages processed correctly before asserting expectations.
2. **Q:** How is the suite resilient to both single and batch payloads?  
   **A:** The `payloads` JSON supports arrays/hooks for sequential payloads, so the same validation logic handles single-object events and multi-item sequences.
3. **Q:** What ensures the HTML report stays actionable?  
   **A:** It reports per-table pass/fail counts, attaches SQL query context, and logs the difference between expected vs actual rows so you know exactly what broke.

## Theory Knowledge for Interviews
- **Event-Driven Architecture:** Understand how Event Hubs forward messages to downstream processors and how to correlate `order_id` or `audit_id` from the payload to persisted rows.
- **Idempotent Validation:** Running the pipeline with `clean → send → validate` ensures repeatability and demonstrates how side effects are managed.
- **Data-Driven Testing:** The tests rely on JSON payloads + expected row definitions so the same code can validate different business rules without code changes.

## Troubleshooting & Tips
- Keep Azure connection strings current; rotating secrets requires updating `config/db_config.json`.
- If the report shows missing rows, query Azure SQL manually (`SELECT * FROM orders WHERE order_id = 'ORD123';`) to verify ingestion.
- Use logs to confirm that an event payload reached Event Hub; failed sends usually show HTTP errors.

## Next Steps
- Extend the runner to publish results directly to Azure DevOps artifacts or send summary emails via `EmailUtils`.
- Add retries and timeout policies around Event Hub publishing to harden flaky cloud operations.
