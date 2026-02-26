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
                int totalCases = 0, totalTables = 0, passedTables = 0, failedTables = 0, skippedTables = 0;
                List<String> failureSummary = new ArrayList<>();

                StringBuilder htmlReport = new StringBuilder(ReportUtils.getHtmlHeader());
                
                // Placeholder for summary cards
                int summaryPos = htmlReport.length();
                htmlReport.append("<!--SUMMARY_CARDS-->");

                htmlReport.append("<div class=\"layout\">\n<aside class=\"sidebar\">\n<h3>Test Scenarios</h3>\n");
                for (EventPayload payload : payloads) {
                    htmlReport.append(String.format("<a class=\"case-link link-%s\" id=\"link-%s\" href=\"#case-%s\">%s</a>\n", 
                        payload.getTest_case_id(), payload.getTest_case_id(), payload.getTest_case_id(), payload.getScenario_name()));
                }
                htmlReport.append("</aside>\n<main class=\"content\">\n");

                for (EventPayload payload : payloads) {
                    totalCases++;
                    boolean caseFailed = false;
                    StringBuilder caseStepsHtml = new StringBuilder();

                    banner(String.format("TEST CASE : %s\nSCENARIO  : %s\nEVENT     : %s\nORDER ID  : %s",
                            payload.getTest_case_id(), payload.getScenario_name(), payload.getEvent_type(), payload.getLookup_ids().get("order_id")));

                    // 1. DB CLEANUP
                    section("DATABASE CLEANUP");
                    caseStepsHtml.append("<div class=\"step\"><div class=\"step-title\">Step 1: Database Cleanup</div><ul>");
                    if (payload.getExpected_tables() != null) {
                        for (String table : payload.getExpected_tables()) {
                            TableSchema schema = schemas.get(table);
                            if (schema != null) {
                                String lookup = schema.getPrimary_lookup();
                                Object value = payload.getLookup_ids().get(lookup);
                                if (value != null) {
                                    DbUtils.deleteTableData(conn, Collections.singletonList(table), lookup, value);
                                    caseStepsHtml.append(String.format("<li>Cleaned table <b>%s</b> for %s=%s</li>", table, lookup, value));
                                }
                            }
                        }
                    }
                    caseStepsHtml.append("</ul></div>");

                    // 2. TRIGGER EVENT
                    section("TRIGGER EVENT");
                    caseStepsHtml.append("<div class=\"step\"><div class=\"step-title\">Step 2: Event Trigger</div>");
                    try {
                        EventHubUtils.triggerEvent(dbConfig, payload.getEvent_payload());
                        caseStepsHtml.append(String.format("<p class=\"pass\">Successfully triggered <b>%s</b> event to Event Hub</p>", payload.getEvent_type()));
                        System.out.println("   [WAIT] Waiting 5 seconds for processing...");
                        Thread.sleep(5000);
                    } catch (Exception e) {
                        System.err.println("   [ERROR] Event trigger failed: " + e.getMessage());
                        caseStepsHtml.append(String.format("<p class=\"fail\">Failed to trigger event: %s</p>", e.getMessage()));
                        caseFailed = true;
                    }
                    caseStepsHtml.append("</div>");

                    // 3. VALIDATION
                    section("VALIDATION");
                    caseStepsHtml.append("<div class=\"step\"><div class=\"step-title\">Step 3: Database Validation</div>");

                    int casePassedTables = 0, caseSkippedTables = 0, caseFailedTables = 0;
                    
                    Map<String, String> tableExpectations = payload.getTable_expectations();
                    if (tableExpectations == null) tableExpectations = new HashMap<>();

                    for (Map.Entry<String, String> entry : tableExpectations.entrySet()) {
                        String table = entry.getKey();
                        String expectation = entry.getValue();

                        if (payload.getExpected_tables() != null && payload.getExpected_tables().contains(table)) continue;

                        totalTables++;
                        TableSchema schema = schemas.get(table);
                        if (schema == null) {
                            failureSummary.add(table + " schema missing");
                            caseFailed = true;
                            failedTables++;
                            caseFailedTables++;
                            caseStepsHtml.append(String.format("<div class='box'><h3>Table : %s</h3><div class='box-content'><p class='fail'>Schema missing</p></div></div>", table));
                            continue;
                        }

                        String lookup = schema.getPrimary_lookup();
                        Object lookupValue = payload.getLookup_ids().get(lookup);

                        List<Map<String, Object>> rows = fetchRows(conn, table, lookup, lookupValue);
                        boolean isValid = ValidationUtils.validateTablePersistence(rows, expectation);

                        if (!isValid) {
                            caseStepsHtml.append(String.format("<div class='box'><h3>Table : %s</h3><div class='box-content'>", table));
                            caseStepsHtml.append(ReportUtils.getHtmlFailureBlock(table, "ROW_PERSISTENCE", expectation, String.format("%d rows found", rows.size()), null));
                            caseStepsHtml.append("</div></div>");
                            failureSummary.add(String.format("%s persistence violation", table));
                            caseFailed = true;
                            failedTables++;
                            caseFailedTables++;
                        } else {
                            skippedTables++;
                            caseSkippedTables++;
                            caseStepsHtml.append(String.format("<div class='box'><h3>Table : %s</h3><div class='box-content'><p class='pass'>[SKIPPED] Presence validation only (%s)</p></div></div>", table, expectation));
                        }
                    }

                    if (payload.getExpected_tables() != null) {
                        for (String table : payload.getExpected_tables()) {
                            totalTables++;
                            boolean tableFailed = false;
                            caseStepsHtml.append(String.format("<div class='box'><h3>Table : %s</h3><div class='box-content'>", table));

                            TableSchema schema = schemas.get(table);
                            if (schema == null) {
                                caseStepsHtml.append("<p class='fail'>Schema missing</p>");
                                tableFailed = true;
                            } else {
                                String lookup = schema.getPrimary_lookup();
                                Object value = payload.getLookup_ids().get(lookup);
                                List<Map<String, Object>> rows = fetchRows(conn, table, lookup, value);

                                if (rows.isEmpty()) {
                                    caseStepsHtml.append(ReportUtils.getHtmlFailureBlock(table, "ROW_PERSISTENCE", "PERSIST", "0 rows found", null));
                                    failureSummary.add(String.format("%s not persisted", table));
                                    tableFailed = true;
                                } else {
                                    // Row data validation
                                    List<Map<String, Object>> expectedRows = JsonUtils.loadExpectedRows(table);
                                    for (Map<String, Object> row : rows) {
                                        Map<String, Object> exp = ValidationUtils.matchExpectedRow(row, expectedRows, schema);
                                        if (exp == null) {
                                            caseStepsHtml.append(ReportUtils.getHtmlFailureBlock(table, "ROW_MATCH", "Expected row", "Not found", null));
                                            tableFailed = true;
                                            continue;
                                        }

                                        if (schema.getMandatory_columns() != null) {
                                            for (String col : schema.getMandatory_columns()) {
                                                if (!ValidationUtils.compareValues(exp.get(col), row.get(col))) {
                                                    caseStepsHtml.append(ReportUtils.getHtmlFailureBlock(table, col, exp.get(col), row.get(col), null));
                                                    tableFailed = true;
                                                } else {
                                                    caseStepsHtml.append(String.format("<p class='pass'>[OK] %s : %s</p>", col, row.get(col)));
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            caseStepsHtml.append("</div></div>");
                            if (tableFailed) {
                                failedTables++;
                                caseFailed = true;
                                caseFailedTables++;
                            } else {
                                passedTables++;
                                casePassedTables++;
                            }
                        }
                    }
                    caseStepsHtml.append("</div>");

                    String statusClass = caseFailed ? "fail" : "pass";
                    htmlReport.append(String.format("<details class=\"case\" id=\"case-%s\" open>\n<summary>\n" +
                                    "  <span class=\"case-id\">%s</span>\n" +
                                    "  <span class=\"case-title\">%s</span>\n" +
                                    "  <span class=\"status %s\">%s</span>\n" +
                                    "</summary>\n<div class=\"case-body\">\n%s\n</div></details>\n",
                            payload.getTest_case_id(), payload.getTest_case_id(), payload.getScenario_name(),
                            statusClass, statusClass.toUpperCase(), caseStepsHtml.toString()));
                }

                String summaryCards = String.format(
                    "<div class=\"summary-cards\">\n" +
                    "  <div class=\"card\"><h3>Total Scenarios</h3><div class=\"value\">%d</div></div>\n" +
                    "  <div class=\"card pass\"><h3>Tables Passed</h3><div class=\"value\">%d</div></div>\n" +
                    "  <div class=\"card fail\"><h3>Tables Failed</h3><div class=\"value\">%d</div></div>\n" +
                    "  <div class=\"card\"><h3>Tables Skipped</h3><div class=\"value\">%d</div></div>\n" +
                    "</div>\n", totalCases, passedTables, failedTables, skippedTables);
                
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
        String sql = String.format("SELECT * FROM %s WHERE %s = ?", table, lookup);
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
