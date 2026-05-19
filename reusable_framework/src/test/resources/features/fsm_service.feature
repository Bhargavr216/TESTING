# ============================================================
# FSM Service — End-to-End Validation
#
# HOW TO ADD A NEW TEST:
#   Just add a new row to the Examples table.
#   No Java code changes needed.
#
# HOW TO REUSE FOR A DIFFERENT SERVICE (e.g. MFS):
#   Create mfs_service.feature, change the table names in steps.
#   No Java code changes needed.
# ============================================================

@FSM
Feature: FSM Service End-to-End Validation

  Background:
    Given I connect to the database
    And I connect to the Event Hub

  # ============================================================
  # TC1 — HAPPY PATH
  # Event triggers → processes → moves to archive → result persists
  # ============================================================
  @TC1 @HappyPath @Smoke
  Scenario Outline: TC1 Happy Path - event "<eventId>" type "<eventType>" processes successfully

    # 1. Send event to FSM
    When I send event with id "<eventId>" and type "<eventType>" from file "<payloadFile>"
    And  I wait <waitSeconds> seconds for processing

    # 2. job_queue must be CLEARED (record moved to archive)
    Then record with "id" = "<eventId>" should NOT exist in "fsm.fsm_job_queue"

    # 3. job_queue_arch must have the record
    And record with "id" = "<eventId>" should exist in "fsm.fsm_job_queue_arch"

    # 4. Validate all columns in archive
    And in "fsm.fsm_job_queue_arch" where "id" = "<eventId>" the columns should be:
      | column      | expected      |
      | event_type  | <eventType>   |
      | job_status  | SUCCESS       |
      | exception   | NULL          |
      | retry_count | 0             |

    # 5. json_response must not be empty
    And the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "<eventId>" should not be empty JSON

    # 6. Validate specific field inside json_response
    And the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "<eventId>"
        field "status" should be "SUCCESS"

    # 7. Validate mandatory attributes in json_response
    And the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "<eventId>"
        should contain mandatory attributes from "<mandatoryFile>"

    # 8. Full JSON match
    And the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "<eventId>"
        should match expected JSON "<expectedJsonFile>"

    # 9. JSON schema validation
    And the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "<eventId>"
        should conform to schema "<schemaFile>"

    # 10. fsm_result must have the record
    And record with "ful_id" = "<eventId>" should exist in "fsm.fsm_result"
    And column "status" in "fsm.fsm_result" where "ful_id" = "<eventId>" should be "SUCCESS"

    Examples:
      | eventId  | eventType     | payloadFile                              | waitSeconds | mandatoryFile                                    | expectedJsonFile                                  | schemaFile                              |
      | EVT-001  | ORDER_CREATED | testdata/payloads/order_created_001.json | 30          | testdata/expected/mandatory/order_mandatory.json | testdata/expected/full/order_001_expected.json    | testdata/schemas/order_schema.json      |
      | EVT-002  | ORDER_CREATED | testdata/payloads/order_created_002.json | 30          | testdata/expected/mandatory/order_mandatory.json | testdata/expected/full/order_002_expected.json    | testdata/schemas/order_schema.json      |
      | EVT-003  | ORDER_UPDATED | testdata/payloads/order_updated_003.json | 30          | testdata/expected/mandatory/order_mandatory.json | testdata/expected/full/order_003_expected.json    | testdata/schemas/order_schema.json      |

  # ============================================================
  # TC2 — FAILURE PATH
  # Bad event → stays in job_queue → exception recorded
  # ============================================================
  @TC2 @FailurePath
  Scenario Outline: TC2 Failure Path - event "<eventId>" type "<eventType>" fails and stays in queue

    # 1. Send bad event
    When I send event with id "<eventId>" and type "<eventType>" from file "<payloadFile>"
    And  I wait <waitSeconds> seconds for processing

    # 2. job_queue_arch must be EMPTY (failure doesn't archive)
    Then record with "id" = "<eventId>" should NOT exist in "fsm.fsm_job_queue_arch"

    # 3. job_queue must STILL have the record
    And record with "id" = "<eventId>" should exist in "fsm.fsm_job_queue"

    # 4. Validate failure columns
    And in "fsm.fsm_job_queue" where "id" = "<eventId>" the columns should be:
      | column     | expected    |
      | event_type | <eventType> |
      | job_status | FAILED      |

    # 5. json_response must be empty (no result on failure)
    And the "json_response" column in "fsm.fsm_job_queue" where "id" = "<eventId>" should be empty JSON

    # 6. exception must NOT be empty
    And column "exception" in "fsm.fsm_job_queue" where "id" = "<eventId>" should not be empty

    # 7. exception must NOT be null
    And column "exception" in "fsm.fsm_job_queue" where "id" = "<eventId>" should not be null

    # 8. retry_count should be 1
    And column "retry_count" in "fsm.fsm_job_queue" where "id" = "<eventId>" should be "1"

    Examples:
      | eventId   | eventType     | payloadFile                               | waitSeconds |
      | EVT-F001  | INVALID_EVENT | testdata/payloads/invalid_event_001.json  | 20          |
      | EVT-F002  | ORDER_CREATED | testdata/payloads/bad_order_002.json      | 20          |
      | EVT-F003  | ORDER_UPDATED | testdata/payloads/bad_order_003.json      | 20          |

  # ============================================================
  # TC3 — RETRY POLLING (async — wait until status changes)
  # ============================================================
  @TC3 @Retry @RetryCount(5) @RetryInterval(10)
  Scenario Outline: TC3 Polling - wait for event "<eventId>" to be archived

    When I send event with id "<eventId>" and type "<eventType>" from file "<payloadFile>"

    # Poll until record appears in archive (up to 5 x 10s = 50s)
    Then record with "id" = "<eventId>" should eventually exist in "fsm.fsm_job_queue_arch"
         within 5 retries every 10 seconds

    # Poll until status is SUCCESS
    And column "job_status" in "fsm.fsm_job_queue_arch" where "id" = "<eventId>"
        should eventually be "SUCCESS" within 5 retries every 10 seconds

    Examples:
      | eventId  | eventType     | payloadFile                              |
      | EVT-P001 | ORDER_CREATED | testdata/payloads/order_created_001.json |
      | EVT-P002 | ORDER_CREATED | testdata/payloads/order_created_002.json |

  # ============================================================
  # TC4 — API VALIDATION
  # ============================================================
  @TC4 @API @Smoke
  Scenario Outline: TC4 API - validate "<endpoint>" returns "<expectedStatus>" with field "<field>" = "<expected>"

    Given I connect to the API
    When  I call GET "<endpoint>" with param "<paramKey>" as "<paramValue>"
    Then  the response status should be <expectedStatus>
    And   the response field "<field>" should be "<expected>"

    Examples:
      | endpoint          | paramKey | paramValue | expectedStatus | field  | expected |
      | /fsm/job/status   | id       | EVT-001    | 200            | status | SUCCESS  |
      | /fsm/job/status   | id       | EVT-002    | 200            | status | SUCCESS  |
      | /fsm/job/status   | id       | EVT-F001   | 200            | status | FAILED   |
      | /fsm/job/details  | id       | EVT-999    | 404            | status | NOT_FOUND|
