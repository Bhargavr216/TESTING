# BDD Framework — Step Reference Guide

> **Who is this for?**
> Anyone writing feature files — testers, BAs, product owners.
> You do NOT need to know Java to use this framework.
> Just pick the step you need from this guide and paste it into your feature file.

---

## How It Works

A feature file is written in plain English. Each line maps to a pre-built action in the framework.
You only need to fill in the values inside the quotes.

```gherkin
Then record with "id" = "EVT-001" should exist in "fsm.fsm_job_queue"
                  ^^^    ^^^^^^^                    ^^^^^^^^^^^^^^^^^^^
               column    value                         table name
```

**To reuse for a different service**, just change the table name:
```gherkin
Then record with "id" = "EVT-001" should exist in "mfs.mfs_job_queue"   ← MFS service
Then record with "id" = "EVT-001" should exist in "xyz.xyz_job_queue"   ← XYZ service
```
Zero code changes. Only the table name changes.

---

## Feature File Structure

Every feature file follows this pattern:

```gherkin
Feature: [What you are testing]

  Background:
    Given I connect to the database
    And I connect to the Event Hub     ← only if sending events

  Scenario Outline: [Test name with "<placeholders>"]
    [steps using <placeholders>]

    Examples:
      | column1 | column2 | ... |
      | value1  | value2  | ... |   ← one row = one test run
      | value3  | value4  | ... |   ← add rows to add more tests
```

---

## SETUP STEPS

These go at the top of a scenario (GIVEN / WHEN).

---

### Connect to database
```gherkin
Given I connect to the database
```
Opens a database connection using the config file for the current environment.

---

### Connect to API
```gherkin
Given I connect to the API
```
Sets up the API base URL from the config file.

---

### Connect to Event Hub
```gherkin
Given I connect to the Event Hub
```
Connects to Azure Event Hub using the config file.

---

### Send an event
```gherkin
When I send event with id "EVT-001" and type "ORDER_CREATED" from file "testdata/payloads/order_001.json"
```
Sends a JSON payload file to the Event Hub.
- `id` — the unique event ID (this is what you'll look up in the DB later)
- `type` — the event type string
- `file` — path to the JSON payload file inside `src/test/resources/`

---

### Call an API endpoint
```gherkin
When I call GET "/orders/status"
When I call GET "/orders" with param "orderId" as "ORD-001"
When I call POST "/orders" with body "testdata/payloads/order_001.json"
When I call PUT "/orders/ORD-001" with body "testdata/payloads/update_001.json"
When I call DELETE "/orders/ORD-001"
```

---

### Wait for processing
```gherkin
And I wait 30 seconds for processing
```
Pauses the test for N seconds. Use this for simple waits.
For smarter waiting, use the **Retry/Polling** steps instead.

---

## DATABASE VALIDATION STEPS

---

## A — EXISTENCE CHECKS

> **Use when:** You want to confirm a record is there (or not there) in a table.

### Record should exist
```gherkin
Then record with "id" = "EVT-001" should exist in "fsm.fsm_job_queue_arch"
Then record with "id" = "EVT-001" should exist in "mfs.mfs_job_queue_arch"
Then record with "ful_id" = "EVT-001" should exist in "fsm.fsm_result"
Then record with "order_id" = "ORD-001" should exist in "orders.order_table"
```
✅ Passes if the record is found.
❌ Fails if the record is missing.

---

### Record should NOT exist
```gherkin
Then record with "id" = "EVT-001" should NOT exist in "fsm.fsm_job_queue"
Then record with "id" = "EVT-001" should NOT exist in "mfs.mfs_job_queue"
```
✅ Passes if the record is NOT found (e.g. queue was cleared after processing).
❌ Fails if the record is still there.

---

## B — ROW COUNT CHECKS

> **Use when:** You want to check exactly how many records exist.

### Exact count
```gherkin
Then table "fsm.fsm_job_queue" should have 0 records with "id" = "EVT-001"
Then table "fsm.fsm_job_queue_arch" should have 1 records with "id" = "EVT-001"
```

### Zero records
```gherkin
Then table "fsm.fsm_job_queue" should have no records with "id" = "EVT-001"
```
Same as checking count = 0. Reads more naturally.

### At least N records
```gherkin
Then table "fsm.fsm_job_queue_arch" should have at least 1 records with "id" = "EVT-001"
```

---

## C — COLUMN VALUE CHECKS

> **Use when:** You want to check what value is stored in a specific column.

### Column equals a value
```gherkin
Then column "job_status"  in "fsm.fsm_job_queue_arch" where "id"     = "EVT-001" should be "SUCCESS"
Then column "job_status"  in "mfs.mfs_job_queue_arch" where "id"     = "EVT-001" should be "SUCCESS"
Then column "status"      in "fsm.fsm_result"         where "ful_id" = "EVT-001" should be "SUCCESS"
Then column "retry_count" in "fsm.fsm_job_queue"      where "id"     = "EVT-F001" should be "1"
Then column "event_type"  in "fsm.fsm_job_queue_arch" where "id"     = "EVT-001" should be "ORDER_CREATED"
```

### Column does NOT equal a value
```gherkin
Then column "job_status" in "fsm.fsm_job_queue" where "id" = "EVT-001" should not be "FAILED"
```

### Column contains a substring
```gherkin
Then column "exception" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should contain "NullPointerException"
Then column "exception" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should contain "Connection refused"
```

### Column starts with a prefix
```gherkin
Then column "event_type" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should start with "ORDER"
```

---

## D — NULL CHECKS

> **Use when:** You want to confirm a column is NULL or NOT NULL in the database.

### Column is NULL
```gherkin
Then column "exception"     in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should be null
Then column "exception"     in "mfs.mfs_job_queue_arch" where "id" = "EVT-001" should be null
Then column "json_response" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should not be null
```

### Column is NOT NULL
```gherkin
Then column "exception"     in "fsm.fsm_job_queue" where "id" = "EVT-F001" should not be null
Then column "json_response" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should not be null
```

---

## E — EMPTY CHECKS

> **Use when:** You want to confirm a column has no value (empty string, blank, or null).
> Most useful for checking `json_response` is empty on failure scenarios.

### Column is empty
```gherkin
Then column "json_response" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be empty
```
✅ Passes if the value is: NULL, blank, `{}`, or `[]`

### Column is NOT empty
```gherkin
Then column "exception"     in "fsm.fsm_job_queue" where "id" = "EVT-F001" should not be empty
Then column "json_response" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should not be empty
```

---

## F — NUMERIC CHECKS

> **Use when:** You want to compare a number column (like retry_count).

```gherkin
Then column "retry_count" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be greater than 0
Then column "retry_count" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be less than 5
Then column "retry_count" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be between 1 and 3
```

---

## G — MULTI-COLUMN CHECK (check many columns at once)

> **Use when:** You want to validate several columns of the same row in one step.
> Much cleaner than writing one step per column.

```gherkin
Then in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" the columns should be:
  | column      | expected      |
  | event_type  | ORDER_CREATED |
  | job_status  | SUCCESS       |
  | exception   | NULL          |
  | retry_count | 0             |
```

Same step, different service:
```gherkin
Then in "mfs.mfs_job_queue_arch" where "id" = "EVT-001" the columns should be:
  | column      | expected      |
  | event_type  | ORDER_CREATED |
  | job_status  | SUCCESS       |
```

---

## H — RETRY / POLLING STEPS

> **Use when:** The system processes events asynchronously and you don't know exactly when it will finish.
> Instead of a fixed wait, these steps keep checking until the condition is met.

### Poll until a column reaches a value
```gherkin
Then column "job_status" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     should eventually be "SUCCESS" within 5 retries every 10 seconds
```
Checks every 10 seconds, up to 5 times (= max 50 seconds total).

### Poll until a record appears
```gherkin
Then record with "id" = "EVT-001" should eventually exist in "fsm.fsm_job_queue_arch"
     within 5 retries every 10 seconds
```

---

## I — CROSS-TABLE CHECKS

> **Use when:** You want to confirm the same value exists consistently across two tables.

```gherkin
Then column "event_type" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     should match column "event_type" in "fsm.fsm_result" where "ful_id" = "EVT-001"
```

---

## JSON VALIDATION STEPS

These steps read a JSON column from the database and validate its content.

---

## J — JSON COLUMN STATE

### JSON column is empty
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue"      where "id" = "EVT-F001" should be empty JSON
Then the "json_response" column in "mfs.mfs_job_queue"      where "id" = "EVT-F001" should be empty JSON
```
Use on failure scenarios — confirms no response was stored.

### JSON column is NOT empty
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should not be empty JSON
```

---

## K — JSON FIELD VALUE CHECKS

> **Use when:** You want to check a specific field inside the JSON stored in a column.
> Supports nested fields using dot-notation: `"order.customer.name"`

### Field equals a value
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     field "status" should be "SUCCESS"

Then the "json_response" column in "fsm.fsm_result" where "ful_id" = "EVT-001"
     field "order.customer.name" should be "John Doe"
```

### Field does NOT equal a value
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue" where "id" = "EVT-001"
     field "status" should not be "FAILED"
```

### Field contains a substring
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     field "message" should contain "processed successfully"
```

### Field is null
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     field "errorCode" should be null
```

### Field is NOT null
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     field "orderId" should not be null
```

---

## L — JSON MANDATORY ATTRIBUTES

> **Use when:** You want to check that certain key fields exist with the right values,
> but you don't care about extra fields in the response.

Create a small JSON file listing only the fields you care about:
```json
{
  "status":    "SUCCESS",
  "eventType": "ORDER_CREATED",
  "orderId":   "ORD-001"
}
```

Then use:
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     should contain mandatory attributes from "testdata/expected/mandatory/order_mandatory.json"
```
✅ Passes if all listed fields exist with matching values.
✅ Extra fields in the actual response are ignored.

---

## M — JSON FULL MATCH

> **Use when:** You want to verify the entire JSON response matches exactly what you expect.

Create a JSON file with the full expected response:
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     should match expected JSON "testdata/expected/full/order_001_expected.json"
```
✅ Every field in the expected file must exist in actual with the same value.
✅ Extra fields in actual are OK (lenient mode).

---

## N — JSON SCHEMA VALIDATION

> **Use when:** You want to validate the structure of the JSON — correct field types,
> required fields present, no unexpected values.

Create a JSON Schema file (ask a developer to help with this once):
```gherkin
Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     should conform to schema "testdata/schemas/order_schema.json"
```
✅ Reports ALL schema violations at once.

---

## API VALIDATION STEPS

---

## O — STATUS CODE CHECKS

```gherkin
Then the response status should be 200
Then the response status should be 201
Then the response status should be 400
Then the response status should be 404
Then the response status should be 500
Then the response should be successful        ← any 2xx
Then the response should be a client error    ← any 4xx
Then the response should be a server error    ← any 5xx
```

---

## P — RESPONSE FIELD CHECKS

```gherkin
Then the response field "status" should be "SUCCESS"
Then the response field "data.order.id" should be "ORD-001"
Then the response field "status" should not be "FAILED"
Then the response field "message" should contain "successfully"
Then the response field "errorCode" should be null
Then the response field "orderId" should not be null
```

---

## Q — RESPONSE BODY CHECKS

```gherkin
Then the response body should not be empty
Then the response body should contain "EVT-001"
Then the response body should contain "ORDER_CREATED"
```

---

## How to Add a New Test (No Code Needed)

1. Open the feature file (e.g. `fsm_service.feature`)
2. Find the right `Scenario Outline`
3. Add a new row to the `Examples` table

**Before:**
```gherkin
Examples:
  | eventId | eventType     | payloadFile                              | waitSeconds | ...
  | EVT-001 | ORDER_CREATED | testdata/payloads/order_created_001.json | 30          | ...
```

**After (added EVT-004):**
```gherkin
Examples:
  | eventId | eventType     | payloadFile                              | waitSeconds | ...
  | EVT-001 | ORDER_CREATED | testdata/payloads/order_created_001.json | 30          | ...
  | EVT-004 | ORDER_CREATED | testdata/payloads/order_created_004.json | 30          | ...
```

Then create the payload file `testdata/payloads/order_created_004.json`. That's it.

---

## How to Reuse for a Different Service

| What to change         | Where                                      | Java code? |
|------------------------|--------------------------------------------|------------|
| Table names            | In the feature file steps                  | ❌ No      |
| Event Hub name         | `application-dev.properties`               | ❌ No      |
| Database connection    | `application-dev.properties`               | ❌ No      |
| API base URL           | `application-dev.properties`               | ❌ No      |
| Payload files          | `testdata/payloads/`                       | ❌ No      |
| Expected JSON files    | `testdata/expected/`                       | ❌ No      |
| Schema files           | `testdata/schemas/`                        | ❌ No      |

---

## How to Run Tests

```bash
# Run all tests (DEV environment)
mvn test

# Run only smoke tests
mvn test -Dcucumber.filter.tags="@Smoke"

# Run only FSM happy path
mvn test -Dcucumber.filter.tags="@FSM and @HappyPath"

# Run only failure path tests
mvn test -Dcucumber.filter.tags="@FailurePath"

# Run against UAT environment
mvn test -Denv=uat -Dcucumber.filter.tags="@Smoke"

# Run a specific scenario by name
mvn test -Dcucumber.filter.tags="@TC1"
```

---

## Available Tags

| Tag             | Meaning                                      |
|-----------------|----------------------------------------------|
| `@Smoke`        | Quick sanity check — run these first         |
| `@HappyPath`    | Tests where everything works correctly       |
| `@FailurePath`  | Tests where the system handles errors        |
| `@Retry`        | Polling tests — retries until condition met  |
| `@API`          | API-only tests                               |
| `@FSM`          | FSM service tests                            |
| `@MFS`          | MFS service tests (create mfs_service.feature)|
| `@TC1`          | Test case 1                                  |
| `@TC2`          | Test case 2                                  |

---

## Project Structure

```
bdd-framework/
├── pom.xml                                      ← Maven build file (don't touch)
└── src/
    ├── main/java/com/framework/
    │   ├── config/        Config.java            ← reads properties files
    │   ├── context/       ScenarioContext.java   ← shares data between steps
    │   ├── hooks/         Hooks.java             ← setup/teardown per scenario
    │   ├── retry/         Retry.java             ← polling logic
    │   ├── steps/         SetupSteps.java        ← GIVEN/WHEN steps
    │   │                  DbSteps.java           ← all DB validation steps
    │   │                  JsonSteps.java         ← all JSON validation steps
    │   │                  ApiSteps.java          ← all API validation steps
    │   └── validators/    DbValidator.java       ← DB queries
    │                      ApiValidator.java      ← REST calls
    │                      JsonValidator.java     ← JSON checks
    │                      EventHubPublisher.java ← sends events
    └── test/
        ├── java/          TestRunner.java        ← runs the tests
        └── resources/
            ├── config/    application-dev.properties   ← DEV config
            │              application-uat.properties   ← UAT config
            ├── features/  fsm_service.feature          ← YOUR TESTS GO HERE
            └── testdata/
                ├── payloads/    ← JSON files to send as events
                ├── expected/
                │   ├── mandatory/  ← required field files
                │   └── full/       ← full expected response files
                └── schemas/        ← JSON Schema files
```
