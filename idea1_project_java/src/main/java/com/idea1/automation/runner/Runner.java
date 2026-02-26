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
            List<EventPayload> payloads = JsonUtils.loadJson("payloads/event_payloads.json", new TypeReference<List<EventPayload>>() {});
            Map<String, TableSchema> schemas = JsonUtils.loadJson("schemas/table_schema.json", new TypeReference<Map<String, TableSchema>>() {});
            DbConfig dbConfig = JsonUtils.loadJson("config/db_config.json", DbConfig.class);

            try (Connection conn = DbUtils.getConnection(dbConfig)) {
                int totalCases = 0, totalTables = 0, passedTables = 0, failedTables = 0, skippedTables = 0;
                List<String> failureSummary = new ArrayList<>();

                StringBuilder htmlReport = new StringBuilder(ReportUtils.getHtmlHeader());
                htmlReport.append("<div class=\"layout\">\n<aside class=\"sidebar\">\n<h3>Project / Testcases</h3>\n");
                for (EventPayload payload : payloads) {
                    htmlReport.append(String.format("<a class=\"case-link\" href=\"#case-%s\">%s</a>\n", payload.getTest_case_id(), payload.getTest_case_id()));
                }
                htmlReport.append("</aside>\n<main class=\"content\">\n");

                for (EventPayload payload : payloads) {
                    totalCases++;
                    boolean caseFailed = false;
                    int casePassedTables = 0, caseSkippedTables = 0, caseFailedTables = 0;

                    banner(String.format("TEST CASE : %s\nSCENARIO  : %s\nEVENT     : %s\nORDER ID  : %s",
                            payload.getTest_case_id(), payload.getScenario_name(), payload.getEvent_type(), payload.getLookup_ids().get("order_id")));

                    htmlReport.append(String.format("<details class=\"case\" id=\"case-%s\" open>\n<summary>\n" +
                                    "  <span class=\"case-id\">%s</span>\n" +
                                    "  <span class=\"case-title\">%s</span>\n" +
                                    "  <span class=\"case-meta\">Event: %s | Order: %s</span>\n" +
                                    "</summary>\n<div class=\"case-body\">\n" +
                                    "<div class=\"case-overview\">\n" +
                                    "<p><b>Scenario:</b> %s</p>\n" +
                                    "<p><b>Event:</b> %s</p>\n" +
                                    "<p><b>Order ID:</b> %s</p>\n" +
                                    "</div>\n",
                            payload.getTest_case_id(), payload.getTest_case_id(), payload.getScenario_name(),
                            payload.getEvent_type(), payload.getLookup_ids().get("order_id"),
                            payload.getScenario_name(), payload.getEvent_type(), payload.getLookup_ids().get("order_id")));

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
                            continue;
                        }

                        String lookup = schema.getPrimary_lookup();
                        Object lookupValue = payload.getLookup_ids().get(lookup);

                        List<Map<String, Object>> rows = fetchRows(conn, table, lookup, lookupValue);
                        boolean isValid = ValidationUtils.validateTablePersistence(rows, expectation);

                        if (!isValid) {
                            htmlReport.append(String.format("<div class='box'><h3>Table : %s</h3>", table));
                            detailedFailure(table, "ROW_PERSISTENCE", expectation, String.format("%d rows found for lookup %s=%s", rows.size(), lookup, lookupValue), null);
                            htmlReport.append(ReportUtils.getHtmlFailureBlock(table, "ROW_PERSISTENCE", expectation, String.format("%d rows found for lookup %s=%s", rows.size(), lookup, lookupValue), null));
                            htmlReport.append("</div>");
                            failureSummary.add(String.format("%s persistence violation for %s=%s", table, lookup, lookupValue));
                            caseFailed = true;
                            failedTables++;
                            caseFailedTables++;
                        } else {
                            System.out.printf("   [SKIPPED] %s data validation (presence check only)%n", table);
                            skippedTables++;
                            caseSkippedTables++;
                            htmlReport.append(String.format("<div class='box'>\n<h3>Table : %s</h3>\n<p class='pass'>[SKIPPED] Presence validation only (%s)</p>\n</div>\n", table, expectation));
                        }
                    }

                    if (payload.getExpected_tables() != null) {
                        for (String table : payload.getExpected_tables()) {
                            totalTables++;
                            boolean tableFailed = false;
                            section(table);
                            htmlReport.append(String.format("<div class='box'><h3>Table : %s</h3>", table));

                            TableSchema schema = schemas.get(table);
                            if (schema == null) {
                                detailedFailure(table, "SCHEMA", "Schema must exist", "Missing", null);
                                continue;
                            }

                            String lookup = schema.getPrimary_lookup();
                            Object value = payload.getLookup_ids().get(lookup);

                            List<Map<String, Object>> rows = fetchRows(conn, table, lookup, value);

                            if (rows.isEmpty()) {
                                detailedFailure(table, "ROW_PERSISTENCE", "PERSIST (rows must exist)", String.format("0 rows found for lookup %s=%s", lookup, value), null);
                                htmlReport.append(ReportUtils.getHtmlFailureBlock(table, "ROW_PERSISTENCE", "PERSIST (rows must exist)", String.format("0 rows found for lookup %s=%s", lookup, value), null));
                                failureSummary.add(String.format("%s not persisted for %s=%s", table, lookup, value));
                                tableFailed = true;
                                htmlReport.append("</div>");
                                failedTables++;
                                caseFailed = true;
                                caseFailedTables++;
                                continue;
                            }

                            // Retry Validation
                            if (payload.getRetry_expectations() != null && payload.getRetry_expectations().containsKey(table)) {
                                String opCol = schema.getSecondary_lookup() != null ? schema.getSecondary_lookup() : "operation";
                                List<Map<String, Object>> retryErrors = ValidationUtils.validateRetryExpectations(rows, lookup, value, payload.getRetry_expectations().get(table), opCol);
                                for (Map<String, Object> err : retryErrors) {
                                    detailedFailure(table, "RETRY_COUNT", String.format("%s should repeat %s times for %s", err.get("operation"), err.get("expected"), err.get("lookup")), String.format("found %s times", err.get("actual")), null);
                                    htmlReport.append(ReportUtils.getHtmlFailureBlock(table, "RETRY_COUNT", String.format("%s should repeat %s times for %s", err.get("operation"), err.get("expected"), err.get("lookup")), String.format("found %s times", err.get("actual")), null));
                                    failureSummary.add(table + ".RETRY_COUNT." + err.get("operation"));
                                    tableFailed = true;
                                }
                            }

                            // Unique Constraints
                            List<Map<String, Object>> duplicates = ValidationUtils.validateUniqueConstraints(rows, schema.getUnique_constraints());
                            for (Map<String, Object> dup : duplicates) {
                                detailedFailure(table, "UNIQUE_CONSTRAINT", dup.get("constraint"), dup.get("key"), null);
                                htmlReport.append(ReportUtils.getHtmlFailureBlock(table, "UNIQUE_CONSTRAINT", dup.get("constraint"), dup.get("key"), null));
                                failureSummary.add(table + " unique violation " + dup.get("constraint"));
                                tableFailed = true;
                            }

                            List<Map<String, Object>> expectedRows = JsonUtils.loadExpectedRows(table);

                            for (Map<String, Object> row : rows) {
                                Map<String, Object> exp = ValidationUtils.matchExpectedRow(row, expectedRows, schema);
                                if (exp == null) {
                                    detailedFailure(table, "ROW_MATCH", "Expected row", "Not found", null);
                                    htmlReport.append(ReportUtils.getHtmlFailureBlock(table, "ROW_MATCH", "Expected row", "Not found", null));
                                    failureSummary.add(table + ".ROW_MATCH");
                                    tableFailed = true;
                                    continue;
                                }

                                if (schema.getMandatory_columns() != null) {
                                    for (String col : schema.getMandatory_columns()) {
                                        // Semantic Rule
                                        if (schema.getSemantic_rules() != null && schema.getSemantic_rules().containsKey(col)) {
                                            TableSchema.SemanticRule rule = schema.getSemantic_rules().get(col);
                                            if ("nullable_presence".equals(rule.getType())) {
                                                if (!ValidationUtils.compareValues(exp.get(col), row.get(col))) {
                                                    detailedFailure(table, col, exp.get(col), row.get(col), null);
                                                    htmlReport.append(ReportUtils.getHtmlFailureBlock(table, col, exp.get(col), row.get(col), null));
                                                    failureSummary.add(table + "." + col);
                                                    tableFailed = true;
                                                } else {
                                                    success(col + " semantic OK");
                                                }
                                                continue;
                                            }
                                        }

                                        // JSON Column
                                        if (schema.getJson_columns() != null && schema.getJson_columns().containsKey(col)) {
                                            TableSchema.JsonColumnConfig cfg = schema.getJson_columns().get(col);
                                            if (!exp.containsKey(col)) {
                                                detailedFailure(table, col, "FIELD SHOULD BE PERSISTED IN EXPECTED FILE", "FIELD NOT PERSISTED IN EXPECTED FILE", null);
                                                htmlReport.append(ReportUtils.getHtmlFailureBlock(table, col, "FIELD SHOULD BE PERSISTED IN EXPECTED FILE", "FIELD NOT PERSISTED IN EXPECTED FILE", null));
                                                failureSummary.add(table + "." + col + " not persisted in expected file");
                                                tableFailed = true;
                                                continue;
                                            }
                                            if (row.get(col) == null) {
                                                detailedFailure(table, col, "JSON VALUE", "NULL", null);
                                                htmlReport.append(ReportUtils.getHtmlFailureBlock(table, col, "JSON VALUE", "NULL", null));
                                                failureSummary.add(table + "." + col);
                                                tableFailed = true;
                                                continue;
                                            }

                                            JsonNode actualJson = mapper.readTree(row.get(col).toString());
                                            JsonNode expectedJson = mapper.valueToTree(exp.get(col));

                                            ValidationUtils.removeIgnoredPaths(actualJson, cfg.getIgnored());
                                            ValidationUtils.removeIgnoredPaths(expectedJson, cfg.getIgnored());

                                            List<String> required = cfg.getRequired();
                                            for (String path : ValidationUtils.checkRequiredJsonPaths(actualJson, required)) {
                                                detailedFailure(table, col, "REQUIRED FIELD", "MISSING", path);
                                                htmlReport.append(ReportUtils.getHtmlFailureBlock(table, col, "REQUIRED FIELD", "MISSING", path));
                                                failureSummary.add(table + "." + col + "." + path);
                                                tableFailed = true;
                                            }

                                            for (String path : ValidationUtils.checkRequiredJsonPaths(expectedJson, required)) {
                                                detailedFailure(table, col, "REQUIRED IN EXPECTED", "MISSING", path);
                                                htmlReport.append(ReportUtils.getHtmlFailureBlock(table, col, "REQUIRED IN EXPECTED", "MISSING", path));
                                                failureSummary.add(table + "." + col + "." + path);
                                                tableFailed = true;
                                            }

                                            for (Map<String, Object> e : ValidationUtils.deepCompare(expectedJson, actualJson, "")) {
                                                detailedFailure(table, col, e.get("expected"), e.get("actual"), (String) e.get("path"));
                                                htmlReport.append(ReportUtils.getHtmlFailureBlock(table, col, e.get("expected"), e.get("actual"), (String) e.get("path")));
                                                failureSummary.add(table + "." + col + "." + e.get("path"));
                                                tableFailed = true;
                                            }
                                            continue;
                                        }

                                        // Generated Column
                                        if (schema.getGenerated_columns() != null && schema.getGenerated_columns().contains(col)) {
                                            if (row.get(col) == null) {
                                                detailedFailure(table, col, "GENERATED VALUE", "NULL", null);
                                                htmlReport.append(ReportUtils.getHtmlFailureBlock(table, col, "GENERATED VALUE", "NULL", null));
                                                failureSummary.add(table + "." + col);
                                                tableFailed = true;
                                            } else {
                                                success(col + " : generated value present");
                                            }
                                            continue;
                                        }

                                        // Normal Column Value Check
                                        if (!ValidationUtils.compareValues(exp.get(col), row.get(col))) {
                                            detailedFailure(table, col, exp.get(col), row.get(col), null);
                                            htmlReport.append(ReportUtils.getHtmlFailureBlock(table, col, exp.get(col), row.get(col), null));
                                            failureSummary.add(table + "." + col);
                                            tableFailed = true;
                                        } else {
                                            success(col + " : " + row.get(col));
                                            htmlReport.append(String.format("<p class='pass'>[OK] %s : %s</p>", col, row.get(col)));
                                        }
                                    }
                                }
                            }
                            htmlReport.append("</div>");
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

                    String caseResultText = "PASSED", caseResultClass = "chip-pass";
                    if (caseFailed) {
                        banner("TEST CASE RESULT : FAILED");
                        caseResultText = "FAILED";
                        caseResultClass = "chip-fail";
                    } else if (caseSkippedTables > 0 && casePassedTables == 0) {
                        banner("TEST CASE RESULT : SKIPPED");
                        caseResultText = "SKIPPED";
                        caseResultClass = "chip-skip";
                    } else {
                        banner("TEST CASE RESULT : PASSED");
                    }

                    htmlReport.append(String.format("<div class=\"case-footer\">\n" +
                                    "  <span class=\"chip %s\">RESULT: %s</span>\n" +
                                    "  <span class=\"chip chip-pass\">PASSED TABLES: %d</span>\n" +
                                    "  <span class=\"chip chip-fail\">FAILED TABLES: %d</span>\n" +
                                    "  <span class=\"chip chip-skip\">SKIPPED TABLES: %d</span>\n" +
                                    "</div>\n" +
                                    "</div>\n" +
                                    "</details>\n",
                            caseResultClass, caseResultText, casePassedTables, caseFailedTables, caseSkippedTables));
                }

                banner("EXECUTION SUMMARY");
                System.out.println("Total Test Cases : " + totalCases);
                System.out.println("Tables Checked  : " + totalTables);
                System.out.println("Tables Skipped  : " + skippedTables);
                System.out.println("Tables Passed   : " + passedTables);
                System.out.println("Tables Failed   : " + failedTables);

                System.out.println("\nFAILURE SUMMARY");
                for (String f : failureSummary) {
                    System.out.println(" - " + f);
                }

                htmlReport.append(ReportUtils.getHtmlFooter());
                ReportUtils.saveReport(htmlReport.toString());
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
