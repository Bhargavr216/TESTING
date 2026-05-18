package com.idea1.automation.model;

import java.util.List;
import java.util.Map;

public class EventPayload {
    private String test_case_id;
    private String scenario_name;
    private String event_type;
    private Map<String, Object> lookup_ids;
    private Map<String, Object> event_payload;
    private List<String> expected_tables;
    private Map<String, String> table_expectations;
    private Map<String, List<RetryExpectation>> retry_expectations;

    public String getTest_case_id() { return test_case_id; }
    public void setTest_case_id(String test_case_id) { this.test_case_id = test_case_id; }
    public String getScenario_name() { return scenario_name; }
    public void setScenario_name(String scenario_name) { this.scenario_name = scenario_name; }
    public String getEvent_type() { return event_type; }
    public void setEvent_type(String event_type) { this.event_type = event_type; }
    public Map<String, Object> getLookup_ids() { return lookup_ids; }
    public void setLookup_ids(Map<String, Object> lookup_ids) { this.lookup_ids = lookup_ids; }
    public Map<String, Object> getEvent_payload() { return event_payload; }
    public void setEvent_payload(Map<String, Object> event_payload) { this.event_payload = event_payload; }
    public List<String> getExpected_tables() { return expected_tables; }
    public void setExpected_tables(List<String> expected_tables) { this.expected_tables = expected_tables; }
    public Map<String, String> getTable_expectations() { return table_expectations; }
    public void setTable_expectations(Map<String, String> table_expectations) { this.table_expectations = table_expectations; }
    public Map<String, List<RetryExpectation>> getRetry_expectations() { return retry_expectations; }
    public void setRetry_expectations(Map<String, List<RetryExpectation>> retry_expectations) { this.retry_expectations = retry_expectations; }

    public static class RetryExpectation {
        private String operation;
        private int count;

        public String getOperation() { return operation; }
        public void setOperation(String operation) { this.operation = operation; }
        public int getCount() { return count; }
        public void setCount(int count) { this.count = count; }
    }
}
