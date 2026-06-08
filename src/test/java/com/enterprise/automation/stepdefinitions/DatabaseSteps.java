package com.enterprise.automation.stepdefinitions;

import com.enterprise.automation.services.DatabaseService;
import com.enterprise.automation.utils.DatabaseQueryBuilder;
import io.cucumber.datatable.DataTable;
import io.cucumber.java.en.Then;

import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;

public class DatabaseSteps {
    private final DatabaseService db = new DatabaseService();
    private static final String DEFAULT_LOOKUP_COLUMN = "event_id";

    @Then("validate the {string} table for the column {string} should be {string} for {string}")
    public void validateTableColumnValue(String table, String column, String expectedValue, String eventId) {
        String sql = DatabaseQueryBuilder.buildSelection(table, List.of(column), DEFAULT_LOOKUP_COLUMN);
        List<Map<String, Object>> rows = db.fetchRow(sql, eventId);
        assertFalse("No row found for event id " + eventId + " in table " + table, rows.isEmpty());
        Object actual = rows.get(0).get(column);
        assertEquals("Column value mismatch for " + column, expectedValue, actual == null ? null : actual.toString());
    }

    @Then("validate the {string} should persist in {string} table")
    public void validateShouldPersistInTable(String eventId, String table) {
        String sql = DatabaseQueryBuilder.buildExistenceQuery(table, DEFAULT_LOOKUP_COLUMN);
        List<Map<String, Object>> rows = db.fetchRow(sql, eventId);
        assertFalse("Expected event " + eventId + " to persist in table " + table, rows.isEmpty());
    }

    @Then("validate the {string} should not persist in {string} table")
    public void validateShouldNotPersistInTable(String eventId, String table) {
        String sql = DatabaseQueryBuilder.buildExistenceQuery(table, DEFAULT_LOOKUP_COLUMN);
        List<Map<String, Object>> rows = db.fetchRow(sql, eventId);
        assertTrue("Expected event " + eventId + " to NOT persist in table " + table, rows.isEmpty());
    }

    @Then("validate the {string} table for {string} with following columns")
    public void validateTableColumnsForEvent(String table, String eventId, DataTable dataTable) {
        List<Map<String, String>> rows = dataTable.asMaps(String.class, String.class);
        for (Map<String, String> expectedRow : rows) {
            List<String> columns = expectedRow.keySet().stream().toList();
            String sql = DatabaseQueryBuilder.buildSelection(table, columns, DEFAULT_LOOKUP_COLUMN);
            List<Map<String, Object>> results = db.fetchRow(sql, eventId);
            assertFalse("No row found for event id " + eventId + " in table " + table, results.isEmpty());
            Map<String, Object> actual = results.get(0);
            expectedRow.forEach((column, expectedValue) -> {
                Object actualValue = actual.get(column);
                if ("null".equalsIgnoreCase(expectedValue)) {
                    assertNull("Expected " + column + " to be null", actualValue);
                } else {
                    assertEquals("Column " + column + " value mismatch", expectedValue, actualValue == null ? null : actualValue.toString());
                }
            });
        }
    }

    @Then("Validate the {string} column in {string} table should be null for {string}")
    public void validateColumnShouldBeNull(String column, String table, String eventId) {
        String sql = DatabaseQueryBuilder.buildSelection(table, List.of(column), DEFAULT_LOOKUP_COLUMN);
        List<Map<String, Object>> rows = db.fetchRow(sql, eventId);
        assertFalse("No row found for event id " + eventId + " in table " + table, rows.isEmpty());
        assertNull("Expected " + column + " to be null", rows.get(0).get(column));
    }

    @Then("Validate the {string} column in {string} table should not be null for {string}")
    public void validateColumnShouldNotBeNull(String column, String table, String eventId) {
        String sql = DatabaseQueryBuilder.buildSelection(table, List.of(column), DEFAULT_LOOKUP_COLUMN);
        List<Map<String, Object>> rows = db.fetchRow(sql, eventId);
        assertFalse("No row found for event id " + eventId + " in table " + table, rows.isEmpty());
        assertNotNull("Expected " + column + " to be not null", rows.get(0).get(column));
    }

    @Then("Validate the {string} table with {string} with the following operations")
    public void validateAuditTableOperations(String table, String eventId, DataTable operations) {
        List<Map<String, String>> rows = operations.asMaps(String.class, String.class);
        for (Map<String, String> row : rows) {
            String operation = row.get("operation");
            String sql = DatabaseQueryBuilder.buildAuditOperationQuery(table, DEFAULT_LOOKUP_COLUMN, "operation");
            List<Map<String, Object>> result = db.fetchRow(sql, eventId, operation);
            assertFalse("Expected operation " + operation + " for event " + eventId + " in table " + table, result.isEmpty());
        }
    }

    @Then("Validate the {string} column response in {string} table for the {string} schema matches the {string}")
    public void validateJsonColumnSchema(String column, String table, String eventId, String schemaFile) {
        String sql = DatabaseQueryBuilder.buildSelection(table, List.of(column), DEFAULT_LOOKUP_COLUMN);
        List<Map<String, Object>> rows = db.fetchRow(sql, eventId);
        assertFalse("No row found for event id " + eventId + " in table " + table, rows.isEmpty());
        Object jsonValue = rows.get(0).get(column);
        assertNotNull("Expected JSON content in column " + column, jsonValue);
        String schemaPath = "expected/schemas/" + schemaFile;
        ApiSteps.validateJsonSchema(jsonValue.toString(), schemaPath);
    }

    @Then("Validate the {string} column response in {string} table for the {string} should contains {string} should be {string}")
    public void validateJsonPathColumnValue(String column, String table, String eventId, String jsonPath, String expectedValue) {
        String sql = DatabaseQueryBuilder.buildSelection(table, List.of(column), DEFAULT_LOOKUP_COLUMN);
        List<Map<String, Object>> rows = db.fetchRow(sql, eventId);
        assertFalse("No row found for event id " + eventId + " in table " + table, rows.isEmpty());
        Object jsonValue = rows.get(0).get(column);
        assertNotNull("Expected JSON content in column " + column, jsonValue);
        ApiSteps.validateJsonPathValue(jsonValue.toString(), jsonPath, expectedValue);
    }
}
