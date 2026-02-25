Feature: Event-driven DB validation

  Scenario: Validate event Event-201 order ORD201 type ORDER_CREATED
    Given mysql host "localhost" port 3306 database "job_processing_db" user "root" password "" and payload file "src/main/resources/payloads/event_payload.json" and expected file "src/main/resources/expected/job_queue_arch_expected_data.json" and schema dir "src/main/resources/schemas"
    Then select event-id "Event-201" and order-id "ORD201"
    Then database values should match expected data

  Scenario: Validate event Event-202 order ORD202 type ORDER_VALIDATED
    Given mysql host "localhost" port 3306 database "job_processing_db" user "root" password "" and payload file "src/main/resources/payloads/event_payload.json" and expected file "src/main/resources/expected/job_queue_arch_expected_data.json" and schema dir "src/main/resources/schemas"
    Then select event-id "Event-202" and order-id "ORD202"
    Then database values should match expected data

  Scenario: Validate event Event-203 order ORD203 type ORDER_FAILED
    Given mysql host "localhost" port 3306 database "job_processing_db" user "root" password "" and payload file "src/main/resources/payloads/event_payload.json" and expected file "src/main/resources/expected/job_queue_arch_expected_data.json" and schema dir "src/main/resources/schemas"
    Then select event-id "Event-203" and order-id "ORD203"
    Then database values should match expected data

  Scenario: Validate event Event-204 order ORD204 type ORDER_QUEUED
    Given mysql host "localhost" port 3306 database "job_processing_db" user "root" password "" and payload file "src/main/resources/payloads/event_payload.json" and expected file "src/main/resources/expected/job_queue_arch_expected_data.json" and schema dir "src/main/resources/schemas"
    Then select event-id "Event-204" and order-id "ORD204"
    Then database values should match expected data

  Scenario: Validate event Event-205 order ORD205 type ORDER_COMPLETED
    Given mysql host "localhost" port 3306 database "job_processing_db" user "root" password "" and payload file "src/main/resources/payloads/event_payload.json" and expected file "src/main/resources/expected/job_queue_arch_expected_data.json" and schema dir "src/main/resources/schemas"
    Then select event-id "Event-205" and order-id "ORD205"
    Then database values should match expected data

