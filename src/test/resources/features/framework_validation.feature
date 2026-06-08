Feature: Event-driven validation framework
  The framework should support event triggering, database validation, and API response checks.

  Scenario: validate fsm_job_queue workflow for event-fsm-01
    Given trigger the event payload "event_01.json"
    Then validate the "fsm_job_queue" table for the column "status" should be "DONE" for "event-fsm-01"
    Then validate the "event-fsm-01" should persist in "fsm_job_queue" table
    Then validate the "event-fsm-01" should not persist in "other_queue" table
    Then validate the "fsm_job_queue" table for "event-fsm-01" with following columns
      | status | exception | retry_count |
      | DONE   | null      | 3           |
    Then Validate the "exception" column in "fsm_job_queue" table should be null for "event-fsm-01"
    Then Validate the "exception" column in "fsm_job_queue" table should not be null for "event-fsm-02"
    And Validate the "fsm-audit" table with "event-fsm-01" with the following operations
      | operation  |
      | open       |
      | in_progress|
      | done       |
    Then Validate the "enrich_state" column response in "fsm_job_queue" table for the "event-fsm-01" schema matches the "schema.json"
    Then Validate the "enrich_state" column response in "fsm_job_queue" table for the "event-fsm-01" should contains "products.data.items.id" should be "1001"
    And Validate the get api "products/1001" status should be "200"
    And Validate the get api "products/1001" response schema matches the "schema.json"
    And validate the get api "products/1001" response data should contains "products.data.items.id" should be "1001"
