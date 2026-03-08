# OTF — Event-Driven Database Validation with BDD

## End-to-End Explanation
This project generates Cucumber scenarios from JSON payloads, triggers Azure-style events, queries MySQL data, and validates the rows against expected JSON. The pipeline is: `FeatureGenerator` builds `target/generated-features/event_validation.feature` from `payloads/event_payload.json`, the BDD runner (`RunCucumberTest`) executes steps in `stepdefinitions/Testautomation.java`, the utilities (`EventTrigger`, `JsonCompare`, `databasecolumnUtil`) drive event submission and per-table validation, and Allure reports and JSON comparison summaries are stored under `target/allure-results`.

## Key Components & Coverage
- **`EventTrigger`**: crafts HTTP payloads and posts them to Event Grid endpoints, ensuring the same event structure is reused.
- **`JsonCompare`**: deep compares actual rows with expected JSON, honoring required/optional fields, allowed values, and JSON path rules.
- **`databasecolumnUtil`**: resolves lookup keys, fetches rows by `id` or `orderid`, and enumerates tables.
- **`FeatureGenerator`**: creates Cucumber features from structured payloads, ensuring tests stay data-driven without manual feature editing.
- **`stepdefinitions/Testautomation.java`**: orchestrates lookups, compares data, logs results, and attaches Allure artifacts.
- **Allure + Cucumber**: test results are published automatically with attachments from JSON comparisons.

## Setup & Execution
1. Install **Java 11+**, **Maven**, and ensure MySQL is reachable.
2. Configure your database connection details inside `src/main/resources/application.properties` or similar configuration entries.
3. Generate the feature file: `mvn test-compile` (the `FeatureGenerator` runs during `generate-test-resources`).
4. Execute the suite: `mvn clean test`.
5. Serve the Allure report: `allure serve target/allure-results`.

## Reporting & Observability
- Allure reports (in `target/allure-results`) display scenario outcomes, attachments (JSON diffs), and step logs.
- `target/generated-features` contains the auto-generated feature for traceability.
- JSON comparison logs highlight missing fields, unexpected nulls, and schema violations for every table.

## Important Interview Questions & Answers
1. **Q:** Why generate Cucumber features instead of writing them manually?  
   **A:** The generator keeps tests synchronized with payload data, reduces duplication, and lets you add new scenarios by editing JSON rather than multiple feature files.
2. **Q:** How do you compare complex JSON columns with expected data?  
   **A:** `JsonCompare.validateTable(...)` handles optional/ignored paths, allowed values, and time formats while producing a structured `ValidationReport`.
3. **Q:** What ensures the framework works across different payloads?  
   **A:** Both the event payloads and schema lookups are decoupled from the code; you can plug in new services simply by adding payloads and schema JSON files.

## Theory Knowledge for Interviews
- **Behavior-Driven Development (BDD):** Translate data scenarios into human-readable feature files, even when they are generated, to keep stakeholders aligned with requirements.
- **Schema and Lookup Driven Validation:** Store lookup combinations and column rules in JSON so the code only interprets them and applies the same validators across tables.
- **Observability via Allure:** The report includes attachments/logs and fosters debugging by exposing the state of each validation step.

## Troubleshooting & Tips
- Update `src/main/resources/payloads/event_payload.json` carefully; invalid JSON structures break the feature generator.
- If Allure reports show missing attachments, verify that `JsonCompare` successfully produced the `ValidationReport` and that the `stepdefinitions` attach it.
- Keep `target/generated-features/event_validation.feature` under inspection when debugging scenario generation issues.

## Next Steps
- Add CI/CD hooks to publish Allure dashboards after each pipeline run.
- Expand the validator to produce structured JSON outputs for downstream analytics systems.
