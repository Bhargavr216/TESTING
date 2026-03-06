# Idea 1 Azure Event Hub -> Database Validation Framework


## 1. PROJECT OVERVIEW
- Problem solved: Validates that every event published into Azure Event Hubs is consumed by downstream services and persisted into Azure SQL Database or PostgreSQL with the expected payload data.
- Project type: Automation and validation framework that triggers cloud events, waits for processing, and compares persisted rows to expected JSON snapshots.
- Technologies:
  - Java 17 + Maven for builds and dependency management.
  - Jackson for parsing JSON configuration, payloads, and expected rows.
  - JDBC drivers for PostgreSQL and Microsoft SQL Server.
  - Azure Event Hubs SDK for sending test events over AMQP WebSockets.
  - Custom HTML reporting with filters and Jira defect links.
- Why these technologies: Java provides enterprise-grade libraries, Maven keeps dependencies consistent, Jackson handles JSON deeply, JDBC and Azure SDK cover messaging and database access, and a single runnable JAR keeps CI/CD steps simple.
- High-level architecture: Runner orchestrates the lifecycle, JsonUtils loads files, PayloadUtils resolves placeholders, EventHubUtils publishes events, DbUtils manages connections, ValidationUtils compares rows, and ReportUtils renders detailed HTML with Jira hooks.
- Systems involved: Azure Event Hub for messaging, downstream microservices for processing, Azure SQL Database or PostgreSQL for persistence, and Jira for defect tracking via the report.
- Simple architecture explanation: The framework loads config and payloads, optionally cleans the database, publishes events, waits for the asynchronous pipeline, queries target tables, validates the data, and produces an HTML report that summarizes every assertion.


## 2. HIGH LEVEL FLOW OF THE SYSTEM
1. Boot and configuration: DbConfig, EventPayload, and TableSchema JSON files are loaded through JsonUtils. The runner chooses either the explicit dbConnectionString or constructs a PostgreSQL URL using host/port credentials.
2. Pre-test cleanup (synchronous): When enableCleanup is true, DbUtils.deleteallTableData executes a hard delete across the service schema and inserts baseline data into service_customer_details. This step runs once before any scenario.
3. Per test case loop:
   - A banner is logged and the report planner reserves markup for the scenario.
   - Trigger event (asynchronous): PayloadUtils.processPlaceholders updates tokens such as {{CURRENT_TIMESTAMP_ISO}}. EventHubUtils.triggerEvent publishes the payload array or object to Azure Event Hub over AMQP WebSockets. The runner then sleeps for 10 seconds (Thread.sleep(10000)) to allow downstream services to process the event.
   - Validation (synchronous): For each table in table_expectations or expected_tables, the framework fetches rows with fetchRows, enforces persistence expectations (PERSIST or NOT_PERSIST), matches rows against expected snapshots, validates nested JSON fields, checks null-presence rules, and runs exception persistence checks.
   - Jira hooks: Failures append to jiraDetails, and the HTML report offers a Raise a Defect button that opens Jira with a pre-filled summary.
4. Reporting: After all scenarios run, summary cards replace a placeholder in the HTML, the report file is written to reports/idea1_report.html, and the console prints the generated path.
- Synchronous vs asynchronous: Cleanup, querying, validation, and report writing are sequential. Publishing to Event Hub is asynchronous, so the runner sleeps instead of polling.
- Retries: The framework does not re-send events automatically. Retry expectations can be captured by expected snapshots or by validating tables such as job_queue that show multiple audit rows.
- Polling: There is no polling loop. Extend the runner with a custom wait or polling loop if downstream processing takes longer than the fixed 10 seconds.
- Validations: Persistence checks, row matching, JSON path validation, semantic rules (nullable_presence and min_value), and null-presence checks feed into the HTML table.

## 3. PROJECT STRUCTURE EXPLANATION
`
/
  config/                  # Runtime configuration (db connection strings, Event Hub, feature toggles)
  db/                      # SQL scripts to create and seed the PostgreSQL schema
  expected/tables/         # Expected row snapshots named <table>_expected_data.json
  payloads/                # payloads/event_payloads.json lists every test scenario
  reports/                 # report output (reports/idea1_report.html)
  schemas/                 # table_schema.json defines per-table validation rules
  src/main/java/com/idea1/automation/
      model/               # POJOs: DbConfig, EventPayload, TableSchema
      runner/              # Runner.java: orchestrator
      utils/               # JsonUtils, PayloadUtils, EventHubUtils, DbUtils, ReportUtils, ValidationUtils
  target/                  # Maven build artifacts (shaded jar, classes)
  logs/                    # Placeholder for future log collection
  pom.xml                  # Maven definition with dependencies and the shade plugin
  PROJECT_DOCS.md          # This document
`
Each folder has a clear role: config controls connectivity, payloads drives scenarios, schemas describes rules, expected/tables stores snapshots, reports holds the HTML summary, and src contains the Java source.


## 4. FILE BY FILE EXPLANATION
- pom.xml: Declares Java 17, dependencies (Jackson, Azure Event Hubs/Identity, PostgreSQL/MSSQL JDBC drivers, JSON schema validator), and the Maven Shade plugin that builds target/automation-1.0-SNAPSHOT.jar with Runner as the main class.
- src/main/java/com/idea1/automation/runner/Runner.java:
  - Purpose: Entry point that loads configs/payloads/schemas, optionally cleans the database, triggers Event Hub events, validates persistence, and renders the HTML report.
  - Key methods: main (orchestrates the run), banner/section (console logging), fetchRows (tries table variants with and without dcc prefixes and builds column lists from TableSchema), and the per-scenario validation logic.
  - Interaction: Orchestrates every utility, writes reports/idea1_report.html, tracks pass/fail counts, and prints debug SQL statements.
- model/DbConfig.java: Deserializes config/db_config.json with database/Event Hub settings, cleanup toggles, and Jira metadata.
- model/EventPayload.java: Represents a test case with test_case_id, scenario_name, event_type, lookup_ids, event_payload, expected_tables, table_expectations, check_exception_persistence, and optional retry_expectations.
- model/TableSchema.java: Defines validation rules per table: primary_lookup, optional secondary_lookup, unique_constraints, mandatory_columns, json_columns with required/ignored paths, semantic_rules, null_presence_check, and table_expectation.
- utils/JsonUtils.java: Loads JSON (loadEventPayloads handles arrays or single objects, loadJson is generic, and loadExpectedRows reads expected/tables/<table>_expected_data.json).
- utils/PayloadUtils.java: Recursively replaces {{CURRENT_TIMESTAMP_ISO}} placeholders so payloads stay dynamic.
- utils/EventHubUtils.java: Sends serialized payloads to Azure Event Hub using EventHubClientBuilder and AMQP over WebSockets.
- utils/DbUtils.java: Creates JDBC connections (prefers dbConnectionString, falls back to host/port credentials), deletes rows by lookup columns, and performs the global cleanup SQL across dcc tables.
- utils/ReportUtils.java: Builds the HTML/CSS/JS header, validation tables, summary cards, and the Jira modal.
- utils/ValidationUtils.java: Implements persistence checks, expected row matching, deep JSON comparison, nested value extraction, semantic comparisons, and null-presence rules.
- config/db_config.json: Example configuration for database and Event Hub credentials plus feature toggles like enableCleanup and enableEventTrigger.
- payloads/event_payloads.json: Lists scenarios with event payloads, lookup IDs, expected_tables, table_expectations, and exception persistence checks.
- schemas/table_schema.json: Details each table’s validation requirements (lookup keys, mandatory fields, JSON paths, semantic rules, null-presence expectations).
- expected/tables/: Contains expected row snapshots named <table>_expected_data.json for row-by-row comparisons.
- db/setup_database.sql: Creates tables (orders, fulfilment, operations, audit_logs, job_queue) and seeds happy path, queue rerouting, and retry scenarios.
- reports/idea1_report.html: Generated after every run; contains filters, validation tables, summary cards, and Jira defect links.
- logs/: Reserved for logs (currently empty).
- target/ and dependency-reduced-pom.xml: Maven build artifacts including the shaded jar and reduced POM.

## 5. DATA FLOW EXPLANATION
1. Payload JSON (payloads/event_payloads.json) defines the event details, lookup IDs, and validation targets.
2. Payload processing (PayloadUtils.processPlaceholders) replaces tokens such as {{CURRENT_TIMESTAMP_ISO}}.
3. Event producer (EventHubUtils.triggerEvent) serializes the payload and sends it to Azure Event Hub.
4. Event Hub delivers the message asynchronously to downstream microservice(s).
5. Downstream service executes business logic and writes data into tables such as dcc_event_handled, dcc_job_queue_arch, orders, and audit_logs.
6. Database queries (DbUtils.fetchRows) read the rows for each table based on schema lookups.
7. Validation framework (ValidationUtils + Runner) compares actual rows to snapshots, validates JSON columns, and runs semantic/null-presence checks.
8. Report generator (ReportUtils) builds the HTML report with validation tables and Jira links.
9. Test results (reports/idea1_report.html) present pass/fail status for every scenario.

## 6. DATABASE VALIDATION LOGIC
- Expected data definition: Place a JSON array in expected/tables/<table>_expected_data.json. Each object must include the primary lookup (and secondary lookup when needed) so ValidationUtils.matchExpectedRow can pair actual rows correctly.
- Actual data fetching: Runner.fetchRows builds a column list from the schema (lookup, mandatory_columns, json_columns), tries multiple table name variants (table, dcc.table, dcc.dcc_table, dcc.tableWithoutUnderscores), and maps result set columns into key/value pairs.
- Comparison logic: validateTablePersistence enforces PERSIST vs NOT_PERSIST expectations; matchExpectedRow pairs rows by lookup keys; compareValues normalizes nulls, compares numbers with BigDecimal, and respects semantic rules such as nullable_presence.
- Lookup validation: The schema’s primary_lookup tells the runner which column corresponds to payload.lookup_ids, keeping the WHERE clause deterministic.
- Cardinality rules: table_expectations (PERSIST, NOT_PERSIST, ABSENT_ON_SUCCESS) define whether rows must exist. Failures populate failureSummary and mark the scenario as failed.
- JSON column validation: json_columns specify required/ignored paths. ValidationUtils.validateJsonColumn removes ignored fields, ensures required paths exist, and performs a deep comparison.
- Mandatory vs ignored attributes: mandatory_columns guarantees key columns are retrieved, while json_columns.ignored identifies fields that can vary.
- Semantic rules and null presence: semantic_rules support nullable_presence or min_value checks, while null_presence_check enforces whether specific columns should be null or not.
- Mismatch reporting: Each failure adds a <tr> row to the validation table with expected and actual values, and jiraDetails collects text for the Raise a Defect button.

## 7. END TO END EXECUTION EXAMPLE
1. Test start: Runner loads payloads/event_payloads.json. Example scenario:
`json
{
   test_case_id: TC_001,
  scenario_name: Create_fulfilment_Scenario,
  event_type: eos.orders.allocated,
  lookup_ids: {
    event_id: event-dcc-07,
    order_id: col-dcc1007
  },
  event_payload: [
    {
      id: event-dcc-07,
      source: EOS,
      type: eos.orders.allocated,
      data: {
        orderId: col-dcc1007,
        status: Allocated
      }
    }
  ],
  expected_tables: [
    dcc_event_handled,
    dcc_job_queue,
    dcc_job_queue_arch,
    dcc_event_consumption_stats,
    dcc_audit,
    dcc_ord_rist_items,
    dcc_active_queue
  ],
  table_expectations: {
    dcc_event_handled: PERSIST,
    dcc_job_queue: NOT_PERSIST,
    dcc_job_queue_arch: PERSIST,
    dcc_event_consumption_stats: PERSIST,
    dcc_audit: PERSIST,
    dcc_ord_rist_items: PERSIST,
    dcc_active_queue: NOT_PERSIST
  }
}
`
2. Event publish: The runner sends the payload array to the configured Event Hub.
3. Downstream service: The consumer updates dcc_event_handled, archives the payload in dcc_job_queue_arch, increments dcc_event_consumption_stats, and writes audit rows or business tables such as orders.
4. Database update: After the wait, Runner.fetchRows reads every table and loads expected snapshots such as expected/tables/orders_expected_data.json.
5. Validation: The framework enforces persistence, matches rows, validates JSON columns, and checks null-presence rules.
6. Result generation: reports/idea1_report.html lists TC_001 with validation steps and offers a Raise a Defect button if failures occurred.

## 8. HOW TO RUN THE PROJECT
1. Clone the repository: git clone <repo> && cd JAVA_IDEA1.
2. Install prerequisites: Java 17+ and Maven.
3. Configure connectivity: edit config/db_config.json.
   - Provide either dbConnectionString (Azure SQL) or host, port, database, user, password (PostgreSQL).
   - Add eventHubConnectionString and eventHubName, or set enableEventTrigger to false to skip publishing.
   - Optionally set jiraBaseUrl and jiraProjectKey for report defect links.
4. Prepare the database: run psql -f db/setup_database.sql or equivalent against your target database.
5. Update payloads/schemas/expected snapshots as needed for your scenarios.
6. Build: mvn clean package to compile and produce target/automation-1.0-SNAPSHOT.jar.
7. Run:
   - Via Maven: mvn exec:java -Dexec.mainClass=" com.idea1.automation.runner.Runner\
 - Or run the jar: java -jar target/automation-1.0-SNAPSHOT.jar
8. Open reports/idea1_report.html in a browser. The console prints REPORT GENERATED: reports/idea1_report.html.


## 9. HOW TO CREATE A NEW TEST CASE
1. Add an entry to payloads/event_payloads.json:
 - Use a unique test_case_id and descriptive scenario_name.
 - Set event_type, lookup_ids (such as order_id and event_id), and the event_payload.
 - List tables to validate via expected_tables and specify table_expectations (PERSIST for rows that should exist, NOT_PERSIST when they should not).
 - Use check_exception_persistence to assert that certain tables contain non-null exception values when failures are expected.
2. Create expected snapshots: for each table with PERSIST, add expected/tables/<table>_expected_data.json with JSON objects that include lookup columns and any mandatory or JSON columns you care about.
3. Update schemas/table_schema.json if the new tables require special rules (JSON column definitions, semantic/null-presence rules).
4. Optionally replace placeholders like {{CURRENT_TIMESTAMP_ISO}} inside your payload for fresh timestamps.
5. Run the framework and review reports/idea1_report.html to see the new scenario’s validations.


## 10. HOW TO EXTEND FRAMEWORK FOR A NEW SERVICE
1. Identify the Event Hub topic and messages consumed by the new service.
2. Describe each test event in payloads/event_payloads.json, with lookup IDs that map to the downstream tables.
3. List expected_tables and provide table_expectations to indicate whether rows should persist.
4. Configure schemas/table_schema.json so each table knows lookup columns, required JSON paths, and null-presence expectations.
5. Create expected snapshots under expected/tables/<table>_expected_data.json.
6. Run the framework to ensure the new validations pass; the report highlights any mismatches.


## 11. HOW TO BUILD THIS FRAMEWORK FROM SCRATCH
1. Create a Maven project (pom.xml) that targets Java 17 and includes dependencies for Jackson, Azure Event Hubs/Identity, JDBC drivers, and Maven Shade.
2. Add POJOs: DbConfig, EventPayload, and TableSchema for Jackson deserialization.
3. Implement utilities:
 - JsonUtils for reading JSON files.
 - PayloadUtils for placeholder replacement.
 - EventHubUtils for publishing messages.
 - DbUtils for JDBC connections and cleanup helpers.
 - ValidationUtils for persistence, JSON, semantic, and null checks.
 - ReportUtils for HTML output with filters and Jira links.
4. Build a Runner that loads configs, triggers events, waits, fetches rows, invokes ValidationUtils, and writes the HTML report.
5. Create directories: config/, payloads/, schemas/, expected/tables/, reports/, and db/ for SQL scripts.
6. Provide SQL scripts in db/ to create necessary tables and seed data.
7. Package the project as a shaded JAR so running java -jar target/automation-1.0-SNAPSHOT.jar works out of the box.

## 12. COMMON ERRORS AND TROUBLESHOOTING
- Event not consumed: Check eventHubConnectionString, eventHubName, and network/firewall rules. If enableEventTrigger is false, the runner skips publishing.
- Database mismatch: Make sure expected/tables/<table>_expected_data.json matches the lookup IDs and includes the mandatory columns. Use reports/idea1_report.html to compare expected and actual values.
- Timeout errors: Increase the post-publish wait or add a custom polling loop if downstream processing takes longer than 10 seconds.
- Connection issues: Verify JDBC credentials and firewall rules for Azure SQL or PostgreSQL connectivity.
- Missing schema definitions: If table_schema.json lacks an entry, the runner reports  schema missing and flags the scenario as failed. Add the missing schema with primary_lookup and mandatory_columns.


## 13. BEST PRACTICES
- Maintain test data: Keep expected snapshots under version control and update them when payload expectations change.
- Scale scenarios: Group payloads by service/event type or swap config files to validate different environments.
- Structure new tests: Use one EventPayload entry per scenario and keep lookup IDs stable for deterministic queries.
- Keep schemas accurate: Update schemas/table_schema.json with new mandatory columns, JSON paths, and null checks as the downstream schema evolves.
- Review reports: Always open reports/idea1_report.html after runs to check filters, statuses, and Jira links.


## 14. VISUAL FLOW DIAGRAMS
Architecture:
Runner -> JsonUtils/Config -> Payloads + Schemas
         -> EventHubUtils -> Azure Event Hub -> Downstream service
         -> DbUtils -> Azure SQL/PostgreSQL
         -> ValidationUtils + ReportUtils -> reports/idea1_report.html

Execution Flow:
1. Load config/payloads/schemas
2. (Optional) DB cleanup
3. Trigger event via EventHubUtils
4. Wait 10 seconds for downstream processing
5. Fetch rows and validate
6. Append PASS/FAIL to HTML
7. Repeat for next payload -> finalize report

Data Flow:
Event Payload JSON -> Event Hub (AMQP) -> Downstream Service -> JDBC SELECT -> Validation Logic -> HTML Report


## 15. SUMMARY
This framework gives a beginner-friendly, end-to-end way to prove that Azure Event Hub events land in the target database with the right data. By editing payloads, schemas, and expected snapshots you can cover any scenario, while Runner handles cleanup, publishing, waiting, fetching, and reporting. To extend it for another service, identify the new events and tables, provide matching snapshots, and rerun; the generated report highlights what passed and what needs investigation. Junior engineers should start by reviewing the sample payload, running the framework once, and then iteratively adding scenarios while observing the validation table in the report.
