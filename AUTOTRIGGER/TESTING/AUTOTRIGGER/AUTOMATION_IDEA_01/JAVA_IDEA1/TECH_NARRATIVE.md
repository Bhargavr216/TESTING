# Tech Narrative – Azure Event Hub to Database Validation Framework

## 1. The Friendly Intro
Think of this repo as a safety net for any microservice that listens to Azure Event Hub messages and writes data to a relational database. Rather than testing just APIs, it sends real events, waits for the consumers to finish their work, and then opens the database to see if the rows look exactly how we expected. You get a full story: event kicked off → service processed it → data saved → validation report with “pass / fail” and even a Jira link for quick investigation.

This write-up is for people who already know basic programming but have never touched this automation before. You should finish reading it with a clear mental picture of every moving part and how a test run unfolds.

## 2. Big Picture Architecture (Casual)
- **Config + Payloads + Schemas** live in plain JSON files. They tell the runner *what to do*, *what to send*, and *how to check* results.
- **Runner** is the conductor: reads configs, publishes events, waits a little, grabs database rows, runs comparisons, and writes the HTML report.
- **Utilities** split responsibilities (JsonUtils, PayloadUtils, EventHubUtils, DbUtils, ValidationUtils, ReportUtils). No single class does everything.
- **Database + Event Hub** are the external systems. The framework sends a message, downstream services pick it up, and the DB persists the outcome.
- **Report** is the final deliverable: a nicely formatted HTML page (`reports/idea1_report.html`) showing what passed, what failed, and what Jira issue you might raise.

So the architecture is basically: `Config + Payloads → Runner → EventHub → Downstream Service → Database → Validation → HTML Report`.

## 3. Flow Narrative (Step-by-step)
1. **Startup** – Runner reads `config/db_config.json`, loads all payloads from `payloads/event_payloads.json`, and loads validation rules from `schemas/table_schema.json`. If `expected/tables` is missing any snapshot, the runner logs a warning but continues with what is available.
2. **Optional cleanup** – If `enableCleanup` is true, Runner asks `DbUtils` to truncate or delete rows from all tables listed in the schema. This is so every scenario starts from a clean slate.
3. **Scenario execution (loop)** – For each `EventPayload` scenario:
   - PayloadUtils replaces dynamic placeholders like `{{CURRENT_TIMESTAMP_ISO}}`. That way every run has fresh timestamps or unique IDs.
   - EventHubUtils serializes the payload (object or array) and sends it to Azure Event Hub over AMQP WebSockets.
   - Runner sleeps for a fixed delay (10 seconds by default). This is the only asynchronous window – we pause instead of polling. If the consumer is slow, you can bump this wait or implement extra polling logic.
   - DbUtils queries each table listed under `expected_tables` or `table_expectations`, using schema-defined lookup columns to fetch the right rows.
   - ValidationUtils compares actual rows to expected snapshots. It honors persistence rules (`PERSIST/NOT_PERSIST`), JSON path requirements, nullable rules, and custom semantics (like `min_value`).
   - Every pass/fail detail is saved into the report and optionally bucketed into Jira-ready text.
4. **Final report** – After all scenarios, ReportUtils fills summary cards, tosses in validation rows, writes `reports/idea1_report.html`, and prints the path to console.

### Synchronous vs Asynchronous
Everything after the publish is synchronous – cleanup, querying, comparisons, report writing all happen in order. Only the message publish (and the downstream processing that follows) is asynchronous, so we simply wait for a fixed duration instead of building complicated polling logic.

### Retries & Error Handling
The framework does not retry events automatically. If retry behavior is important, build a scenario that publishes the same event twice (or more) and validate audit tables or job queues that track retries.

### Validation Summary
Validation happens after persistence. Expected rows (under `expected/tables`) tell ValidationUtils what the “right answer” looks like, and schema files tell it how to read JSON columns, what columns must exist, and what semantic rules to apply.

## 4. Example Flows
### Positive Scenario (Everything passes)
1. Payload `TC_POSITIVE_ORDER` defines an allocation event where `event_type = orders.allocated` and lookup IDs include `event_id` and `order_id`.
2. Runner publishes the payload to Event Hub.
3. Downstream service processes the event, writes rows into `orders`, `job_queue`, and `audit_logs`.
4. After 10 seconds, Runner reads these tables, matches the rows to `expected/tables/orders_expected_data.json`, `job_queue_expected_data.json`, etc.
5. ValidationUtils confirms all values match (JSON paths, mandatory columns, nullable rules) and marks scenario as PASS.
6. Report shows green cards, validation tables with “pass”, and nothing else is marked for Jira.

### Negative Scenario (Failure captured)
1. Payload `TC_NEGATIVE_ORDER` sends an event but downstream service writes an incorrect status (say `status = “failed”` instead of `status = “allocated”`).
2. Runner fetches table rows and compares them to the expected snapshot.
3. Validation learns the status column differs, adds a row with expected vs actual values, and tags the scenario as FAIL.
4. HTML report highlights the failed row, populates the “Raise a Defect” modal with a summary, and Jira details include the scenario name + failure reason.

### Retry Scenario (Simulates a re-delivery)
1. Payload `TC_RETRY_ORDER` triggers the same event three times, simulating duplicate delivery.
2. The downstream service writes audit entries showing each retry and the job queue may keep multiple records.
3. Validation expects multiple rows in tables like `retry_log` or `job_queue`, so the snapshots contain several objects (one per retry).
4. Runner finds multiple actual rows, matches them to the order of expected snapshots, and confirms retry metrics (timestamps, statuses) match your rules.

Example payload snippet (positive scenario):
```json
{
  "test_case_id": "TC_POSITIVE_ORDER",
  "scenario_name": "Order is allocated once",
  "event_type": "orders.allocated",
  "lookup_ids": {
    "event_id": "evt-1001",
    "order_id": "ord-1001"
  },
  "event_payload": [
    {
      "id": "evt-1001",
      "source": "orders.system",
      "type": "orders.allocated",
      "payload": {
        "orderId": "ord-1001",
        "status": "ALLOCATED"
      }
    }
  ],
  "expected_tables": ["orders", "job_queue", "audit_logs"],
  "table_expectations": {
    "orders": "PERSIST",
    "job_queue": "NOT_PERSIST",
    "audit_logs": "PERSIST"
  }
}
```

## 5. Folder and Component Map
- `/config`: `db_config.json` holds database/Event Hub credentials plus toggles (`enableCleanup`, `enableEventTrigger`, Jira metadata).
- `/payloads`: `event_payloads.json` contains all test scenarios, each with payload bodies, switches, and lookup IDs.
- `/schemas`: Defines the validation rules per table (lookup columns, JSON paths, semantic rules, null expectations).
- `/expected/tables`: JSON snapshots like `orders_expected_data.json` that describe the exact rows you expect.
- `/reports`: Output directory (`idea1_report.html` is the goal post for each run).
- `/db`: SQL script `setup_database.sql` for creating tables in PostgreSQL or Azure SQL.
- `/src`: Java classes grouped by package:
  - `model` holds `DbConfig`, `EventPayload`, `TableSchema`.
  - `runner` owns the `Runner` orchestrator.
  - `utils` holds helpers (JsonUtils, PayloadUtils, EventHubUtils, DbUtils, ValidationUtils, ReportUtils).
- `/target`: Maven artifacts (shaded JAR, compiled classes).

## 6. Component Responsibilities (Simple Terms)
- **Runner** – Reads configs, cleans data, triggers events, waits, collects rows, validates, and writes the report. It also tracks pass/fail counters and builds Jira text for failures.
- **JsonUtils** – Reads any JSON file and hands over POJOs to the runner. It loads payloads, configs, and expected snapshots.
- **PayloadUtils** – Replaces placeholders (like `{{CURRENT_TIMESTAMP_ISO}}`) so payloads stay dynamic each run without editing the files.
- **EventHubUtils** – Sends the payload over AMQP WebSockets into Azure Event Hub. It handles arrays/single objects.
- **DbUtils** – Opens JDBC connections (using dbConnectionString or host/port creds), clears tables when required, and runs SELECT queries for validation.
- **ValidationUtils** – Compares expected vs actual rows, handles JSON column comparisons, enforces semantic/null rules, and organizes mismatch details for the report.
- **ReportUtils** – Builds the HTML page with filters, validation tables, Jira modal, and summary cards.

## 7. Data Flow (Plain Story)
1. The scenario you wrote in `payloads/event_payloads.json` becomes the event payload.
2. PayloadUtils injects dynamic values and EventHubUtils sends it to Azure Event Hub.
3. Downstream services pick up the event and write rows to the database.
4. After waiting (Thread.sleep), DbUtils queries the tables defined in the schema, using lookup columns to match rows.
5. ValidationUtils compares the actual rows to snapshots in `expected/tables`.
6. ReportUtils collects the results and writes `reports/idea1_report.html`, which is the final meter stick.

## 8. Validation Details
- **Expected data** lives in `expected/tables/<table>_expected_data.json`. Each object must contain the lookup columns so Runner can join expected rows with actual ones.
- **Actual data** is fetched via `Runner.fetchRows`, which uses schema settings to build SELECT statements (including JSON columns and mandatory fields).
- **Comparison** uses lookup keys, BigDecimal normalization for numbers, semantic rules (e.g., `nullable_presence`, `min_value`), and JSON column validation that respects ignored/required paths.
- **Persistence expectations** (`PERSIST`, `NOT_PERSIST`, `ABSENT_ON_SUCCESS`) define whether rows must exist. Failures get logged into the HTML report and raise the scenario’s pass/fail flag.
- **Cardinality** is captured by the number of expected objects. Adding two objects means you expect at least two rows.
- **JSON columns** specify nested paths — the framework removes ignored nodes before comparing and ensures required fields exist.
- **Mismatch reporting** populates the validation table with expected vs actual values and appends human-readable text to the Jira modal so the engineer filing the ticket gets context.

## 9. Running the Project (Command-by-command)
1. Clone the repo: `git clone <repo> && cd JAVA_IDEA1`.
2. Install Java 17+ and Maven; verify with `java -version` and `mvn -version`.
3. Update `config/db_config.json`:
   - Provide either `dbConnectionString` or host/port credentials.
   - Supply `eventHubConnectionString`, `eventHubName`, and optional Jira fields.
   - Toggle `enableCleanup` or `enableEventTrigger`.
4. Prepare the database using `psql -f db/setup_database.sql` (PostgreSQL) or equivalent in Azure SQL.
5. Build: `mvn clean package`.
6. Run:
   - Maven: `mvn exec:java -Dexec.mainClass="com.idea1.automation.runner.Runner"`
   - Or fat JAR: `java -jar target/automation-1.0-SNAPSHOT.jar`
7. Open `reports/idea1_report.html` in your browser to see the outcome.

## 10. Adding a New Scenario
1. Create a new object (scenario) inside `payloads/event_payloads.json`. Give it a unique `test_case_id`, scenario name, `event_type`, `lookup_ids`, payload body, `expected_tables`, and `table_expectations`.
2. Create or update snapshots in `expected/tables` for every table you expect to validate. Include lookup columns and every column you care about.
3. Update `schemas/table_schema.json` if you introduce a new table, JSON column, or nullable rule.
4. Run the framework and check `reports/idea1_report.html` for PASS/FAIL and mismatch details.

## 11. Troubleshooting (Casual Tone)
- EventHub not reachable? Double-check `eventHubConnectionString`, `eventHubName`, and network access. Look for AMQP errors in the console.
- Validation fails? Compare the expected snapshot with actual rows shown under the scenario in the HTML report. Update snapshots or payload lookups if they drifted.
- Timeout? The runner waits 10 seconds. If your consumer needs more time, increase the sleep or add a polling loop.
- Missing schema? If `table_schema.json` lacks a definition, the runner logs it and marks the scenario as failed. Add the entry to fix it.
- JDBC errors? Verify database credentials, firewall rules, and whether the database is reachable.

## 12. Visual Flows (ASCII art)
### Architecture
```
 config + payloads + schemas
             ↓
          Runner
     ↙     ↓      ↘
 JsonUtils EventHub Utils DbUtils + Validation
             ↓                ↓
       Azure Event Hub → Downstream service
                          ↓
                 Azure SQL / PostgreSQL
                          ↓
                ReportUtils → reports/idea1_report.html
```

### Execution Flow
```
Load configs + payloads → Optional cleanup → Publish event → Wait (~10s) → Fetch rows → Validate → Write report
```

### Data Flow
```
Payload JSON → EventHubUtils → Azure Event Hub → Downstream service → Database tables → DbUtils SELECT → Validation → HTML report
```

## 13. Closing Thoughts
This narrative is your roadmap: open a payload, run the runner, check the report, and use the diagrams whenever you need to explain the flow. When you add new services, just plug in the new events, expected tables, and schema rules – the runner handles the rest and gives you a detailed HTML verdict for every scenario.
