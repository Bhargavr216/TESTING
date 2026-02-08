Feature: Event-driven DB validation

  Scenario: Validate DB data for event payload
    Given mysql host "localhost" port 3306 database "job_processing_db" user "root" password "" and payload file "src/main/resources/payloads/event_payload.json" and expected file "src/main/resources/expected/job_queue_arch_expected_data.json" and schema dir "src/main/resources/schemas"
    Then database values should match expected data
