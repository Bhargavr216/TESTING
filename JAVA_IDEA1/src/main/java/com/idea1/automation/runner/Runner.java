package com.idea1.automation.runner;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.idea1.automation.model.DbConfig;
import com.idea1.automation.model.EventPayload;
import com.idea1.automation.model.TableSchema;
import com.idea1.automation.utils.*;

import java.io.IOException;
import java.sql.*;
import java.util.*;

public class Runner {
    private static final ObjectMapper mapper = new ObjectMapper();

    public static void main(String[] args) {
        try {
            List<EventPayload> payloads = JsonUtils.loadEventPayloads("payloads/event_payloads.json");
            Map<String, TableSchema> schemas = JsonUtils.loadJson("schemas/table_schema.json", new TypeReference<Map<String, TableSchema>>() {});
            DbConfig dbConfig = JsonUtils.loadJson("config/db_config.json", DbConfig.class);

            try (Connection conn = DbUtils.getConnection(dbConfig)) {
                int totalCases = 0, passedScenarios = 0, failedScenarios = 0;
                List<String> failureSummary = new ArrayList<>();

                StringBuilder htmlReport = new StringBuilder(ReportUtils.getHtmlHeader());

                // Placeholder for summary cards
                int summaryPos = htmlReport.length();
                htmlReport.append("<!--SUMMARY_CARDS-->");

                // Layout with an empty sidebar; sidebar will be populated by report JS so we can attach filters and scrolling
                htmlReport.append("<div class=\"layout\">\n<aside class=\"sidebar\">\n<h3>Test Scenarios</h3>\n</aside>\n<main class=\"content\">\n");

                // Perform one-time DB cleanup before running test cases
                DbUtils.deleteallTableData(conn);
                htmlReport.append("<div class='step'><div class='step-title'>Pre-test DB Cleanup</div><p>All tables were cleared once before tests started.</p></div>");

                for (EventPayload payload : payloads) {
                    totalCases++;
                    boolean scenarioFailed = false;
                    StringBuilder caseStepsHtml = new StringBuilder();
                    StringBuilder validationTable = new StringBuilder();

                    banner(String.format("TEST CASE : %s\nSCENARIO  : %s\nEVENT     : %s\nORDER ID  : %s",
                            payload.getTest_case_id(), payload.getScenario_name(), payload.getEvent_type(), payload.getLookup_ids().get("orderId")));

                    // Note: DB cleanup is performed once before the test run (see report header)
                    caseStepsHtml.append("<div class='step'><div class='step-title'>Pre-test DB Cleanup</div><p>Database was cleared at test start (one-time).</p></div>");

                    // 2. TRIGGER EVENT
                    section("TRIGGER EVENT");
                    caseStepsHtml.append("<div class=\"step\"><div class=\"step-title\">Step 2: Event Trigger</div>");
                    try {
                        EventHubUtils.triggerEvent(dbConfig, payload.getEvent_payload());
                        caseStepsHtml.append(String.format("<p class=\"pass\">Successfully triggered <b>%s</b> event to Event Hub</p>", payload.getEvent_type()));
                        System.out.println("   [WAIT] Waiting 10 seconds for processing...");
                        Thread.sleep(10000);
                    } catch (Exception e) {
                        System.err.println("   [ERROR] Event trigger failed: " + e.getMessage());
                        caseStepsHtml.append(String.format("<p class=\"fail\">Failed to trigger event: %s</p>", e.getMessage()));
                        scenarioFailed = true;
                    }
                    caseStepsHtml.append("</div>");

                    // 3. VALIDATION
                    section("VALIDATION");
                    caseStepsHtml.append("<div class=\"step\"><div class=\"step-title\">Step 3: Database Validation</div>");
                    
                    validationTable.append("<table class='validation-table'><thead><tr><th>Table</th><th>Column</th><th>Expected</th><th>Actual</th><th>Result</th></tr></thead><tbody>");
                    
                    Map<String, String> tableExpectations = payload.getTable_expectations();
                    if (tableExpectations == null) tableExpectations = new HashMap<>();

                    for (Map.Entry<String, String> entry : tableExpectations.entrySet()) {
                        String table = entry.getKey();
                        String expectation = entry.getValue();

                        if (payload.getExpected_tables() != null && payload.getExpected_tables().contains(table)) continue;

                        TableSchema schema = schemas.get(table);
                        if (schema == null) {
                            failureSummary.add(table + " schema missing");
                            scenarioFailed = true;
                            validationTable.append(String.format("<tr><td>%s</td><td colspan='3'>Schema missing</td><td class='fail'>FAIL</td></tr>", table));
                            continue;
                        }

                        String lookup = schema.getPrimary_lookup();
                        Object lookupValue = payload.getLookup_ids().get(lookup);

                        List<Map<String, Object>> rows = fetchRows(conn, table, lookup, lookupValue);
                        boolean isValid = ValidationUtils.validateTablePersistence(rows, expectation);

                        if (!isValid) {
                            failureSummary.add(String.format("%s persistence violation", table));
                            scenarioFailed = true;
                            validationTable.append(String.format("<tr><td>%s</td><td>Persistence</td><td>%s</td><td>%d rows found</td><td class='fail'>FAIL</td></tr>", 
                                table, expectation, rows.size()));
                        } else {
                            validationTable.append(String.format("<tr><td>%s</td><td>Persistence</td><td>%s</td><td>Valid</td><td class='skip'>SKIP</td></tr>", 
                                table, expectation));
                        }
                    }

                    if (payload.getExpected_tables() != null) {
                        for (String table : payload.getExpected_tables()) {
                            boolean tableFailed = false;

                            TableSchema schema = schemas.get(table);
                            if (schema == null) {
                                validationTable.append(String.format("<tr><td>%s</td><td colspan='3'>Schema missing</td><td class='fail'>FAIL</td></tr>", table));
                                scenarioFailed = true;
                                tableFailed = true;
                            } else {
                                String lookup = schema.getPrimary_lookup();
                                Object value = payload.getLookup_ids().get(lookup);
                                List<Map<String, Object>> rows = fetchRows(conn, table, lookup, value);

                                if (rows.isEmpty()) {
                                    validationTable.append(String.format("<tr><td>%s</td><td>Persistence</td><td>PERSIST</td><td>0 rows found</td><td class='fail'>FAIL</td></tr>", table));
                                    failureSummary.add(String.format("%s not persisted", table));
                                    tableFailed = true;
                                    scenarioFailed = true;
                                } else {
                                    // Row data validation
                                    List<Map<String, Object>> expectedRows = JsonUtils.loadExpectedRows(table);
                                    for (Map<String, Object> row : rows) {
                                        Map<String, Object> exp = ValidationUtils.matchExpectedRow(row, expectedRows, schema);
                                        if (exp == null) {
                                            validationTable.append(String.format("<tr><td>%s</td><td>Row Match</td><td>Expected row</td><td>Not found</td><td class='fail'>FAIL</td></tr>", table));
                                            tableFailed = true;
                                            scenarioFailed = true;
                                            continue;
                                        }

                                        if (schema.getMandatory_columns() != null) {
                                            for (String col : schema.getMandatory_columns()) {
                                                // Check if this is a JSON column with field-level validation
                                                if (schema.getJson_columns() != null && schema.getJson_columns().containsKey(col)) {
                                                    TableSchema.JsonColumnConfig jsonConfig = schema.getJson_columns().get(col);
                                                    List<Map<String, Object>> jsonErrors = ValidationUtils.validateJsonColumn(
                                                        exp.get(col), row.get(col), 
                                                        jsonConfig.getRequired(), jsonConfig.getIgnored()
                                                    );
                                                    
                                                    if (jsonErrors.isEmpty()) {
                                                        validationTable.append(String.format("<tr><td>%s</td><td>%s</td><td>Valid JSON</td><td>Valid JSON</td><td class='pass'>PASS</td></tr>", table, col));
                                                    } else {
                                                        for (Map<String, Object> jsonError : jsonErrors) {
                                                            String path = (String) jsonError.get("path");
                                                            Object exp_val = jsonError.get("expected");
                                                            Object act_val = jsonError.get("actual");
                                                            validationTable.append(String.format("<tr><td>%s</td><td>%s.%s</td><td>%s</td><td>%s</td><td class='fail'>FAIL</td></tr>", 
                                                                table, col, path, exp_val, act_val));
                                                        }
                                                        tableFailed = true;
                                                        scenarioFailed = true;
                                                    }
                                                } else {
                                                    // Regular column validation
                                                    boolean colMatch = ValidationUtils.compareValues(exp.get(col), row.get(col));
                                                    String result = colMatch ? "PASS" : "FAIL";
                                                    String resultClass = colMatch ? "pass" : "fail";
                                                    if (!colMatch) {
                                                        tableFailed = true;
                                                        scenarioFailed = true;
                                                    }
                                                    validationTable.append(String.format("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='%s'>%s</td></tr>", 
                                                        table, col, exp.get(col), row.get(col), resultClass, result));
                                                }
                                            }
                                        }

                                        // Null presence checks
                                        if (schema.getNull_presence_check() != null) {
                                            Map<String, Object> nullCheckResult = ValidationUtils.validateNullPresence(schema.getNull_presence_check(), row);
                                            if (!(boolean) nullCheckResult.get("passed")) {
                                                tableFailed = true;
                                                scenarioFailed = true;
                                            }
                                            @SuppressWarnings("unchecked")
                                            List<Map<String, Object>> nullErrors = (List<Map<String, Object>>) nullCheckResult.get("errors");
                                            for (Map<String, Object> error : nullErrors) {
                                                String col = (String) error.get("column");
                                                Object exp_val = error.get("expected");
                                                Object act_val = error.get("actual");
                                                String resultClass = "fail";
                                                validationTable.append(String.format("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='%s'>FAIL</td></tr>", 
                                                    table, col, exp_val, act_val, resultClass));
                                            }
                                            // Add passing null checks to table as well
                                            for (String col : schema.getNull_presence_check().keySet()) {
                                                boolean found = false;
                                                for (Map<String, Object> error : nullErrors) {
                                                    if (col.equals(error.get("column"))) {
                                                        found = true;
                                                        break;
                                                    }
                                                }
                                                if (!found) {
                                                    Object actualValue = row.get(col);
                                                    String expectation = schema.getNull_presence_check().get(col);
                                                    String actualDisplay = actualValue == null ? "null" : actualValue.toString();
                                                    validationTable.append(String.format("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='pass'>PASS</td></tr>", 
                                                        table, col, expectation, actualDisplay));
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    validationTable.append("</tbody></table>");
                    caseStepsHtml.append(validationTable);
                    caseStepsHtml.append("</div>");

                    String statusClass = scenarioFailed ? "fail" : "pass";
                    htmlReport.append(String.format("<details class=\"case\" id=\"case-%s\" open>\n<summary>\n" +
                                    "  <span class=\"case-id\">%s</span>\n" +
                                    "  <span class=\"case-title\">%s</span>\n" +
                                    "  <span class=\"status %s\">%s</span>\n" +
                                    "</summary>\n<div class=\"case-body\">\n%s\n</div></details>\n",
                            payload.getTest_case_id(), payload.getTest_case_id(), payload.getScenario_name(),
                            statusClass, statusClass.toUpperCase(), caseStepsHtml.toString()));
                    
                    if (scenarioFailed) {
                        failedScenarios++;
                    } else {
                        passedScenarios++;
                    }
                }

                String summaryCards = String.format(
                    "<div class=\"summary-cards\">\n" +
                    "  <div class=\"card\"><h3>Total Scenarios</h3><div class=\"value\">%d</div></div>\n" +
                    "  <div class=\"card pass\"><h3>Scenarios Passed</h3><div class=\"value\">%d</div></div>\n" +
                    "  <div class=\"card fail\"><h3>Scenarios Failed</h3><div class=\"value\">%d</div></div>\n" +
                    "</div>\n", totalCases, passedScenarios, failedScenarios);
                
                int placeholderIdx = htmlReport.indexOf("<!--SUMMARY_CARDS-->");
                htmlReport.replace(placeholderIdx, placeholderIdx + 20, summaryCards);

                htmlReport.append("</main></div></body></html>");
                try (java.io.FileWriter writer = new java.io.FileWriter("reports/idea1_report.html")) {
                    writer.write(htmlReport.toString());
                }
                System.out.println("\nREPORT GENERATED: reports/idea1_report.html");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static void banner(String text) {
        System.out.println("\n" + "=".repeat(80));
        System.out.println(text);
        System.out.println("=".repeat(80));
    }

    private static void section(String title) {
        System.out.println("\nTABLE : " + title);
        System.out.println("-".repeat(80));
    }

    private static void success(String msg) {
        System.out.println("   [OK] " + msg);
    }

    private static void detailedFailure(String table, String column, Object expected, Object actual, String path) {
        System.out.println("   [FAILURE]");
        System.out.println("      Table   : " + table);
        System.out.println("      Column  : " + column);
        if (path != null) System.out.println("      Path    : " + path);
        if (expected != null) System.out.println("      Expected: " + expected);
        if (actual != null) System.out.println("      Actual  : " + actual);
    }

    private static List<Map<String, Object>> fetchRows(Connection conn, String table, String lookup, Object value) throws SQLException {
        List<Map<String, Object>> rows = new ArrayList<>();
        String sql = String.format("SELECT * FROM dcc.%s WHERE %s = ?", table, lookup);
        try (PreparedStatement stmt = conn.prepareStatement(sql)) {
            stmt.setObject(1, value);
            try (ResultSet rs = stmt.executeQuery()) {
                ResultSetMetaData meta = rs.getMetaData();
                int colCount = meta.getColumnCount();
                while (rs.next()) {
                    Map<String, Object> row = new HashMap<>();
                    for (int i = 1; i <= colCount; i++) {
                        row.put(meta.getColumnName(i), rs.getObject(i));
                    }
                    rows.add(row);
                }
            }
        }
        return rows;
    }
}
