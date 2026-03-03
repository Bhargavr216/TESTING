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

                StringBuilder htmlReport = new StringBuilder(ReportUtils.getHtmlHeader(dbConfig.getJiraBaseUrl(), dbConfig.getJiraProjectKey()));

                // Placeholder for summary cards
                int summaryPos = htmlReport.length();
                htmlReport.append("<!--SUMMARY_CARDS-->");

                // Layout with an empty sidebar; sidebar will be populated by report JS so we can attach filters and scrolling
                htmlReport.append("<div class=\"layout\">\n<aside class=\"sidebar\">\n<h3>Test Scenarios</h3>\n</aside>\n<main class=\"content\">\n");

                // Perform one-time DB cleanup before running test cases if enabled
                if (dbConfig.isEnableCleanup()) {
                    DbUtils.deleteallTableData(conn);
                    htmlReport.append("<div class='step'><div class='step-title'>Pre-test DB Cleanup</div><p>All tables were cleared once before tests started.</p></div>");
                } else {
                    htmlReport.append("<div class='step'><div class='step-title'>Pre-test DB Cleanup</div><p>Cleanup was disabled via config.</p></div>");
                }

                for (EventPayload payload : payloads) {
                    totalCases++;
                    boolean scenarioFailed = false;
                    StringBuilder caseStepsHtml = new StringBuilder();
                    StringBuilder validationTable = new StringBuilder();
                    StringBuilder jiraDetails = new StringBuilder();

                    banner(String.format("TEST CASE : %s\nSCENARIO  : %s\nEVENT     : %s\nORDER ID  : %s",
                            payload.getTest_case_id(), payload.getScenario_name(), payload.getEvent_type(), payload.getLookup_ids().get("order_id")));

                    // Note: DB cleanup is performed once before the test run (see report header)
                    caseStepsHtml.append("<div class='step'><div class='step-title'>Pre-test DB Cleanup</div><p>Database was cleared at test start (one-time).</p></div>");

                    // 2. TRIGGER EVENT
                    section("TRIGGER EVENT");
                    caseStepsHtml.append("<div class=\"step\"><div class=\"step-title\">Step 2: Event Trigger</div>");
                    try {
                        if (dbConfig.isEnableEventTrigger()) {
                            EventHubUtils.triggerEvent(dbConfig, payload.getEvent_payload());
                            caseStepsHtml.append(String.format("<p class=\"pass\">Successfully triggered <b>%s</b> event to Event Hub</p>", payload.getEvent_type()));
                            System.out.println("   [WAIT] Waiting 10 seconds for processing...");
                            Thread.sleep(10000);
                        } else {
                            caseStepsHtml.append("<p class=\"pass\">Event trigger was <b>SKIPPED</b> via config</p>");
                            System.out.println("   [SKIP] Event trigger disabled.");
                        }
                    } catch (Exception e) {
                        System.err.println("   [ERROR] Event trigger failed: " + e.getMessage());
                        caseStepsHtml.append(String.format("<p class=\"fail\">Failed to trigger event: %s</p>", e.getMessage()));
                        scenarioFailed = true;
                        jiraDetails.append("Event Trigger Failed: ").append(e.getMessage()).append("\\n");
                    }
                    caseStepsHtml.append("</div>");

                    // 3. VALIDATION
                    section("VALIDATION");
                        caseStepsHtml.append("<div class=\"step\"><div class=\"step-title\">Step 3: Database Validation</div>");
                        caseStepsHtml.append("<div class='step-controls'><button class='step-toggle' data-target='val-" + payload.getTest_case_id() + "'>Show Validation</button>" +
                            "<div class='step-filters'><button class='step-filter active' data-target='val-" + payload.getTest_case_id() + "' data-filter='all'>All</button>" +
                            "<button class='step-filter' data-target='val-" + payload.getTest_case_id() + "' data-filter='pass'>Passed</button>" +
                            "<button class='step-filter' data-target='val-" + payload.getTest_case_id() + "' data-filter='fail'>Failed</button>" +
                            "<button class='step-filter' data-target='val-" + payload.getTest_case_id() + "' data-filter='skip'>Skipped</button></div></div>");
                    
                    validationTable.append("<table class='validation-table'><thead><tr><th>Table</th><th>Column</th><th>Expected</th><th>Actual</th><th>Result</th></tr></thead><tbody>");
                    
                    // Combine all tables to validate
                    Set<String> allTables = new LinkedHashSet<>();
                    if (payload.getTable_expectations() != null) {
                        allTables.addAll(payload.getTable_expectations().keySet());
                    }
                    if (payload.getExpected_tables() != null) {
                        allTables.addAll(payload.getExpected_tables());
                    }

                    for (String table : allTables) {
                        TableSchema schema = schemas.get(table);
                        if (schema == null) {
                            failureSummary.add(table + " schema missing");
                            scenarioFailed = true;
                            validationTable.append(String.format("<tr><td>%s</td><td colspan='3'>Schema missing</td><td class='fail'>FAIL</td></tr>", table));
                            jiraDetails.append("Table ").append(table).append(": Schema missing\\n");
                            continue;
                        }

                        String expectation = payload.getTable_expectations() != null ? payload.getTable_expectations().get(table) : null;
                        // If not in table_expectations but in expected_tables, default to PERSIST
                        if (expectation == null && payload.getExpected_tables() != null && payload.getExpected_tables().contains(table)) {
                            expectation = "PERSIST";
                        }
                        if (expectation == null) expectation = "PERSIST"; 

                        String lookup = schema.getPrimary_lookup();
                        Object lookupValue = payload.getLookup_ids().get(lookup);

                        List<Map<String, Object>> rows = fetchRows(conn, table, lookup, lookupValue, schema);
                        boolean persistenceValid = ValidationUtils.validateTablePersistence(rows, expectation);
                        String persistenceResult = persistenceValid ? "PASS" : "FAIL";
                        String persistenceClass = persistenceValid ? "pass" : "fail";

                        if (!persistenceValid) {
                            failureSummary.add(String.format("%s persistence violation", table));
                            scenarioFailed = true;
                            jiraDetails.append("Table ").append(table).append(": Persistence violation (Expected: ").append(expectation).append(", Found: ").append(rows.size()).append(" rows)\\n");
                        }
                        
                        validationTable.append(String.format("<tr><td>%s</td><td>Persistence</td><td>%s</td><td>%d rows found</td><td class='%s'>%s</td></tr>", 
                            table, expectation, rows.size(), persistenceClass, persistenceResult));

                        // If it should persist and it does, perform deeper validation
                        if ("PERSIST".equals(expectation) && !rows.isEmpty()) {
                            List<Map<String, Object>> expectedRows = JsonUtils.loadExpectedRows(table);
                            Set<Integer> matchedDbIndices = new HashSet<>();

                            for (Map<String, Object> exp : expectedRows) {
                                int matchIdx = ValidationUtils.findMatch(exp, rows, matchedDbIndices, schema);
                                if (matchIdx == -1) {
                                    validationTable.append(String.format("<tr><td>%s</td><td>Row Match</td><td>%s</td><td>Not found in DB</td><td class='fail'>FAIL</td></tr>", 
                                        table, exp.get(schema.getPrimary_lookup())));
                                    scenarioFailed = true;
                                    jiraDetails.append("Table ").append(table).append(": Row with ").append(schema.getPrimary_lookup()).append("=").append(exp.get(schema.getPrimary_lookup())).append(" not found in DB\\n");
                                    continue;
                                }

                                matchedDbIndices.add(matchIdx);
                                Map<String, Object> row = rows.get(matchIdx);

                                if (schema.getMandatory_columns() != null) {
                                    for (String col : schema.getMandatory_columns()) {
                                        // Check if this is a JSON column with field-level validation defined in schema
                                        if (schema.getJson_columns() != null && schema.getJson_columns().containsKey(col)) {
                                            TableSchema.JsonColumnConfig jsonConfig = schema.getJson_columns().get(col);
                                            List<Map<String, Object>> jsonErrors = ValidationUtils.validateJsonColumn(
                                                exp.get(col), row.get(col), 
                                                jsonConfig.getRequired(), jsonConfig.getIgnored()
                                            );
                                            
                                            // Show individual required attribute results if defined
                                            if (jsonConfig.getRequired() != null && !jsonConfig.getRequired().isEmpty()) {
                                                for (String path : jsonConfig.getRequired()) {
                                                    boolean foundError = false;
                                                    for (Map<String, Object> error : jsonErrors) {
                                                        if (path.equals(error.get("path"))) {
                                                            foundError = true;
                                                            Object exp_val = error.get("expected");
                                                            Object act_val = error.get("actual");
                                                            validationTable.append(String.format("<tr><td>%s</td><td>%s.%s</td><td>%s</td><td>%s</td><td class='fail'>FAIL</td></tr>", 
                                                                table, col, path, exp_val, act_val));
                                                            jiraDetails.append("Table ").append(table).append(", Column ").append(col).append(".").append(path).append(": Expected ").append(exp_val).append(", Actual ").append(act_val).append("\\n");
                                                            break;
                                                        }
                                                    }
                                                    if (!foundError) {
                                                        Object val = ValidationUtils.getNestedValue(row.get(col), path);
                                                        validationTable.append(String.format("<tr><td>%s</td><td>%s.%s</td><td>Match</td><td>%s</td><td class='pass'>PASS</td></tr>", 
                                                            table, col, path, val != null ? val : "null"));
                                                    }
                                                }
                                            } else if (jsonErrors.isEmpty()) {
                                                validationTable.append(String.format("<tr><td>%s</td><td>%s</td><td>Valid JSON</td><td>Valid JSON</td><td class='pass'>PASS</td></tr>", table, col));
                                            } else {
                                                for (Map<String, Object> jsonError : jsonErrors) {
                                                    String path = (String) jsonError.get("path");
                                                    Object exp_val = jsonError.get("expected");
                                                    Object act_val = jsonError.get("actual");
                                                    validationTable.append(String.format("<tr><td>%s</td><td>%s.%s</td><td>%s</td><td>%s</td><td class='fail'>FAIL</td></tr>", 
                                                        table, col, path, exp_val, act_val));
                                                    jiraDetails.append("Table ").append(table).append(", Column ").append(col).append(".").append(path).append(": Expected ").append(exp_val).append(", Actual ").append(act_val).append("\\n");
                                                }
                                            }
                                            
                                            if (!jsonErrors.isEmpty()) {
                                                scenarioFailed = true;
                                            }
                                        } else {
                                            // Handle nested path if col contains dots or is just a regular column
                                            Object expectedValue;
                                            Object actualValue;

                                            if (col.contains(".")) {
                                                String[] parts = col.split("\\.", 2);
                                                String baseCol = parts[0];
                                                String path = parts[1];
                                                
                                                if (row.containsKey(baseCol)) {
                                                    expectedValue = ValidationUtils.getNestedValue(exp.get(baseCol), path);
                                                    actualValue = ValidationUtils.getNestedValue(row.get(baseCol), path);
                                                } else {
                                                    expectedValue = exp.get(col);
                                                    actualValue = row.get(col);
                                                }
                                            } else {
                                                expectedValue = exp.get(col);
                                                actualValue = row.get(col);
                                            }

                                            // Check if this column has a "nullable_presence" semantic rule
                                            boolean presenceOnly = false;
                                            if (schema.getSemantic_rules() != null && schema.getSemantic_rules().containsKey(col)) {
                                                TableSchema.SemanticRule rule = schema.getSemantic_rules().get(col);
                                                if ("nullable_presence".equalsIgnoreCase(rule.getType())) {
                                                    presenceOnly = true;
                                                }
                                            }

                                            boolean colMatch = ValidationUtils.compareValues(expectedValue, actualValue, presenceOnly);
                                            String result = colMatch ? "PASS" : "FAIL";
                                            String resultClass = colMatch ? "pass" : "fail";
                                            if (!colMatch) {
                                                scenarioFailed = true;
                                                jiraDetails.append("Table ").append(table).append(", Column ").append(col).append(": Expected ").append(expectedValue).append(", Actual ").append(actualValue).append("\\n");
                                            }
                                            
                                            String expectedDisplay = presenceOnly ? (expectedValue == null ? "null" : "not null") : String.valueOf(expectedValue);
                                            String actualDisplay = presenceOnly ? (actualValue == null ? "null" : "not null") : String.valueOf(actualValue);

                                            validationTable.append(String.format("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='%s'>%s</td></tr>", 
                                                table, col, expectedDisplay, actualDisplay, resultClass, result));
                                        }
                                    }
                                }

                                // Null presence checks (Merge schema-level and scenario-level checks)
                                Map<String, String> mergedNullChecks = new HashMap<>();
                                if (schema.getNull_presence_check() != null) {
                                    mergedNullChecks.putAll(schema.getNull_presence_check());
                                }
                                if (payload.getNull_checks() != null && payload.getNull_checks().containsKey(table)) {
                                    mergedNullChecks.putAll(payload.getNull_checks().get(table));
                                }

                                if (!mergedNullChecks.isEmpty()) {
                                    Map<String, Object> nullCheckResult = ValidationUtils.validateNullPresence(mergedNullChecks, row);
                                    if (!(boolean) nullCheckResult.get("passed")) {
                                        scenarioFailed = true;
                                    }
                                    @SuppressWarnings("unchecked")
                                    List<Map<String, Object>> nullErrors = (List<Map<String, Object>>) nullCheckResult.get("errors");
                                    for (Map<String, Object> error : nullErrors) {
                                        String col = (String) error.get("column");
                                        Object exp_val = error.get("expected");
                                        Object act_val = error.get("actual");
                                        validationTable.append(String.format("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='fail'>FAIL</td></tr>", 
                                            table, col, exp_val, act_val));
                                        jiraDetails.append("Table ").append(table).append(", Column ").append(col).append(" (Null Check): Expected ").append(exp_val).append(", Actual ").append(act_val).append("\\n");
                                    }
                                    // Add passing null checks
                                    for (String col : mergedNullChecks.keySet()) {
                                        boolean isError = false;
                                        for (Map<String, Object> e : nullErrors) { if (col.equals(e.get("column"))) { isError = true; break; } }
                                        if (!isError) {
                                            Object actualValue = row.get(col);
                                            String expectationVal = mergedNullChecks.get(col);
                                            validationTable.append(String.format("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='pass'>PASS</td></tr>", 
                                                table, col, expectationVal, actualValue == null ? "null" : actualValue));
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    validationTable.append("</tbody></table>");
                    caseStepsHtml.append("<div id='val-" + payload.getTest_case_id() + "' class='validation-container' style='display:none;'>");
                    caseStepsHtml.append(validationTable);
                    caseStepsHtml.append("</div>");

                    if (scenarioFailed) {
                        String payloadJson = mapper.writeValueAsString(payload.getEvent_payload()).replace("\"", "\\\"");
                        caseStepsHtml.append(String.format("<button class='btn-jira' onclick=\"raiseJiraDefect('%s', '%s', '%s')\">Raise a Defect</button>",
                            payload.getTest_case_id(), payload.getScenario_name(), jiraDetails.toString().replace("'", "\\'").replace("\"", "\\\"")));
                    }
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

    private static List<Map<String, Object>> fetchRows(Connection conn, String table, String lookup, Object value, TableSchema schema) throws SQLException {
        List<Map<String, Object>> rows = new ArrayList<>();
        // Try both with and without dcc. prefix if it fails
        String[] tableNames = {table, "dcc." + table, "dcc.dcc_" + table, "dcc." + table.replace("_", "")};
        SQLException lastEx = null;

        for (String tableName : tableNames) {
            // Build explicit column list if possible to avoid metadata s_1 issues
            String cols = "*";
            if (schema != null) {
                Set<String> allCols = new LinkedHashSet<>();
                allCols.add(lookup);
                if (schema.getMandatory_columns() != null) allCols.addAll(schema.getMandatory_columns());
                if (schema.getJson_columns() != null) allCols.addAll(schema.getJson_columns().keySet());
                // Remove any nulls or empty strings
                allCols.remove(null);
                allCols.remove("");
                if (!allCols.isEmpty()) {
                    cols = String.join(", ", allCols);
                }
            }

            String sql = String.format("SELECT %s FROM %s WHERE %s = ?", cols, tableName, lookup);
            System.out.println("   [DEBUG] Executing: " + sql + " with value: " + value);
            try (PreparedStatement stmt = conn.prepareStatement(sql)) {
                if (value == null) {
                    stmt.setNull(1, java.sql.Types.VARCHAR);
                } else {
                    stmt.setObject(1, value);
                }
                
                try (ResultSet rs = stmt.executeQuery()) {
                    ResultSetMetaData meta = rs.getMetaData();
                    int colCount = meta.getColumnCount();
                    while (rs.next()) {
                        Map<String, Object> row = new HashMap<>();
                        for (int i = 1; i <= colCount; i++) {
                            // Try multiple ways to get the column name
                            String colName = meta.getColumnLabel(i);
                            // Fallback to getColumnName
                            if (colName == null || colName.toLowerCase().matches("s_?\\d+")) {
                                String name = meta.getColumnName(i);
                                if (name != null && !name.toLowerCase().matches("s_?\\d+")) {
                                    colName = name;
                                }
                            }
                            
                            // Last resort: if still s_1, use the column we requested by index!
                            if ((colName == null || colName.toLowerCase().matches("s_?\\d+")) && schema != null) {
                                // This is dangerous but better than s_1
                                // We can't easily know which requested column maps to which index if cols was "*"
                                // but if we built "cols", we know the order!
                            }

                            if (colName != null) {
                                row.put(colName, rs.getObject(i));
                            }
                        }
                        if (row.isEmpty()) {
                            System.out.println("   [DEBUG] Row found but no columns were mapped correctly.");
                        } else {
                            System.out.println("   [DEBUG] Row mapped columns: " + row.keySet());
                        }
                        rows.add(row);
                    }
                    if (!rows.isEmpty()) return rows; // Success!
                }
            } catch (SQLException e) {
                lastEx = e;
                System.out.println("   [DEBUG] Attempt with " + tableName + " failed: " + e.getMessage());
                // Continue to next table name attempt
            }
        }
        
        if (lastEx != null) {
            System.err.println("   [SQL ERROR] Fetch failed for table " + table + ": " + lastEx.getMessage());
        }
        return rows;
    }
}
