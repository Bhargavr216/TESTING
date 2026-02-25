# OTF - Event DB Validation

## Overview
This folder contains a Java-based event-driven database validation project. It compares rows in MySQL tables against expected JSON data and schema rules, and produces Cucumber/Allure test reports.

The project uses:
- Java 11
- Maven
- Cucumber (BDD)
- JUnit 4 runner
- Jackson (JSON parsing)
- MySQL Connector/J
- Allure reporting

## Project Structure
```
OTF/
  src/
    main/
      java/
        utilities/
          EventTrigger.java
          JsonCompare.java
          databasecolumnUtil.java
      resources/
        payloads/             # Input event payloads (JSON)
        expected/             # Expected DB rows per table (JSON arrays)
        schemas/              # Column and lookup schemas (JSON)
    test/
      java/
        stepdefinitions/
          Testautomation.java
        test/
          RunCucumberTest.java
        utils/
          FeatureGenerator.java
      resources/
        event_validation.feature
  target/
    generated-features/       # Auto-generated Cucumber feature file
    allure-results/           # Allure raw results
```

## Core Components

### EventTrigger
File: `OTF/src/main/java/utilities/EventTrigger.java`
- `azureEventTrigger(connectionString, payloadPath)`
  - Reads the payload JSON from disk.
  - Extracts the HTTP endpoint from an Azure Event Grid style connection string.
  - Sends the payload via `HttpClient` POST.

### JsonCompare
File: `OTF/src/main/java/utilities/JsonCompare.java`
- `validateTable(sourceSystem, eventId, tableName, actualRows, expectedArrayNode, schema)`
  - Compares each row of DB data against expected JSON for a table.
  - Produces a `ValidationReport` with pass/fail/skipped results.
- Handles:
  - Required vs optional fields
  - Allowed values
  - Null rules
  - Time and datetime format validation
  - JSON columns (including required/optional/ignored JSON paths)
- Supports per-column rules loaded from `schemas/<table>_<column>.schema.json`.

### databasecolumnUtil
File: `OTF/src/main/java/utilities/databasecolumnUtil.java`
- `fetchByLookup(...)`
  - Selects DB rows using `id` and/or `orderid` (or configured lookup columns).
- `listTables(...)`
  - Lists tables in the target database.
- `fetchByIdOrOrderId(...)`
  - Convenience query using `id` or `orderid` columns.

### FeatureGenerator
File: `OTF/src/test/java/utils/FeatureGenerator.java`
- Generates Cucumber scenarios from `payloads/event_payload.json`.
- Output is written to `target/generated-features/event_validation.feature`.
- This is wired into Maven `generate-test-resources` phase.

### Cucumber Step Definitions
File: `OTF/src/test/java/stepdefinitions/Testautomation.java`
- Loads payloads, expected data, and schemas.
- Resolves lookup columns (from `schemas/<table>_lookup.json` if present).
- Queries the database for matching rows.
- Uses `JsonCompare` to validate and aggregates results.
- Writes a consolidated log to Allure as an attachment.

### Test Runner
File: `OTF/src/test/java/test/RunCucumberTest.java`
- JUnit 4 runner for Cucumber.
- Uses Allure Cucumber plugin.

## Schemas and Expected Data
- Expected data files are named:
  - `src/main/resources/expected/<table>_expected_data.json`
  - Each file is a JSON array; each element is a row.
- Lookup configuration (optional):
  - `src/main/resources/schemas/<table>_lookup.json`
  - Defines `idColumn` and `orderIdColumn`.
- Column rules (optional):
  - `src/main/resources/schemas/<table>_<column>.schema.json`
  - Define JSON requirements, allowed values, time patterns, etc.

## Running the Tests
Run from the repository root (where `pom.xml` exists):

```bash
mvn clean test
```

This will:
1. Generate the feature file from `event_payload.json`.
2. Execute Cucumber tests.
3. Write Allure results to `target/allure-results`.

To view Allure reports (if Allure CLI is installed):

```bash
allure serve target/allure-results
```

## Notes
- Update DB connection settings in the generated feature file or modify `FeatureGenerator.java` defaults.
- Large `target/` and report files may be environment-specific.