package stepdefinitions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import io.qameta.allure.Allure;
import utilities.EventTrigger;
import utilities.JsonCompare;
import utilities.JsonCompare.ValidationReport;
import utilities.databasecolumnUtil;

import java.nio.file.Path;
import java.sql.SQLException;
import java.util.*;

public class Testautomation {
    private final ObjectMapper mapper = new ObjectMapper();
    private final EventTrigger eventTrigger = new EventTrigger();
    private final databasecolumnUtil dbUtil = new databasecolumnUtil();
    private final JsonCompare jsonCompare = new JsonCompare();

    private static final String TABLE_NAME = "job_queue_arch";
    private static final String ID_COLUMN = "id";
    private static final String ORDER_ID_COLUMN = "orderid";

    private String host;
    private int port;
    private String database;
    private String user;
    private String password;
    private String payloadPath;
    private String expectedPath;
    private String schemaDir;
    private JsonNode payloadArray;
    private String selectedEventId;
    private String selectedOrderId;
    private final StringBuilder scenarioLog = new StringBuilder();

    private final List<ValidationReport> reports = new ArrayList<>();
    private final Map<String, JsonCompare.ColumnRule> columnRuleCache = new HashMap<>();

    @Given("mysql host {string} port {int} database {string} user {string} password {string} and payload file {string} and expected file {string} and schema dir {string}")
    public void setup(String host, int port, String db, String user, String password, String payload, String expected, String schemaDir) throws Exception {
        this.host = host;
        this.port = port;
        this.database = db;
        this.user = user;
        this.password = password;
        this.payloadPath = payload;
        this.expectedPath = expected;
        this.schemaDir = schemaDir;
        this.payloadArray = mapper.readTree(Path.of(payload).toFile());
    }

    @When("event is triggered")
    public void triggerEvent() throws Exception {
        // Event triggering intentionally skipped; validation reads IDs from payload file directly.
    }

    @Then("select event-id {string} and order-id {string}")
    public void selectEvent(String eventId, String orderId) {
        this.selectedEventId = eventId;
        this.selectedOrderId = orderId;
    }

    @Then("database values should match expected data")
    public void validateDatabase() throws Exception {
        if (!payloadArray.isArray()) {
            throw new IllegalArgumentException("Payload file must be a JSON array");
        }
        Set<String> payloadEventIds = new HashSet<>();
        Set<String> payloadOrderIds = new HashSet<>();
        for (JsonNode payloadNode : payloadArray) {
            payloadEventIds.add(payloadNode.path("event-id").asText());
            payloadOrderIds.add(payloadNode.path("order-id").asText());
        }

        for (JsonNode payloadNode : payloadArray) {
            String eventId = payloadNode.path("event-id").asText();
            String orderId = payloadNode.path("order-id").asText();
            if (selectedEventId != null && !selectedEventId.isEmpty()) {
                if (!selectedEventId.equals(eventId) || !selectedOrderId.equals(orderId)) {
                    continue;
                }
            }
            System.out.println("[Scenario - event_id - " + eventId + " and order-id " + orderId + " ] =>");
            logScenario("Scenario event-id=" + eventId + " order-id=" + orderId);

            

            List<ExpectedTable> tables = loadExpectedTables(payloadEventIds, payloadOrderIds);
            if (tables.isEmpty()) {
                throw new IllegalStateException("No expected files found in expected directory. Validation cannot proceed.");
            }

            List<String> dbTables = dbUtil.listTables(host, port, database, user, password);
            List<String> missingExpected = new ArrayList<>();
            for (String t : dbTables) {
                Path expectedFile = Path.of(Path.of(expectedPath).getParent().toString(), t + "_expected_data.json");
                if (!java.nio.file.Files.exists(expectedFile)) {
                    missingExpected.add(t);
                }
            }
            if (!missingExpected.isEmpty()) {
                throw new IllegalStateException("Expected file missing for tables: " + String.join(", ", missingExpected));
            }

            for (ExpectedTable table : tables) {
                JsonNode expectedRow = table.expectedById.containsKey(eventId) ? table.expectedById.get(eventId) : table.expectedByOrder.get(orderId);
                if (expectedRow == null) {
                    continue;
                }
                System.out.println("TableName - " + table.tableName);
                logScenario("Table: " + table.tableName);

                LookupConfig lookup = resolveLookup(table.tableName, expectedRow);
                List<Map<String, Object>> actualRows;
                try {
                    actualRows = dbUtil.fetchByLookup(
                            host,
                            port,
                            database,
                            user,
                            password,
                            table.tableName,
                            lookup.idColumn,
                            eventId,
                            lookup.orderIdColumn,
                            orderId
                    );
                } catch (SQLException ex) {
                    throw new RuntimeException("DB fetch failed for table " + table.tableName, ex);
                }
                // log("DB: rows fetched=" + actualRows.size());

                enrichSchemaWithColumnRules(table.tableName, table.schema, expectedRow);
                JsonNode expectedArray = mapper.createArrayNode().add(expectedRow);
                ValidationReport report = jsonCompare.validateTable("phpmyadmin", eventId, table.tableName, actualRows, expectedArray, table.schema);
                reports.add(report);
                printScenarioTableSummary(report);
            }
        }

        // String reportJson = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(reports);
        // System.out.println(reportJson);

        for (ValidationReport r : reports) {
            if ("FAIL".equals(r.status)) {
                // defer assertion to print consolidated failure summary
            }
        }

        printFailedSummary(reports);
        Allure.addAttachment("validation-log", "text/plain", scenarioLog.toString());

        for (ValidationReport r : reports) {
            if ("FAIL".equals(r.status)) {
                throw new AssertionError("Validation failed for table " + r.tableName);
            }
        }
    }

    // logs suppressed

   private void enrichSchemaWithColumnRules(String tableName, JsonCompare.Schema schema, JsonNode expectedRow) throws Exception {
    Iterator<String> fields = expectedRow.fieldNames();
    while (fields.hasNext()) {
        String column = fields.next();
        JsonNode value = expectedRow.get(column);

        // Only try schema for JSON-like columns
        boolean looksJson = value.isObject() || value.isArray() ||
                (value.isTextual() && (value.asText().trim().startsWith("{") || value.asText().trim().startsWith("[")));
        if (!looksJson) {
            continue;
        }

        String fileName = tableName + "_" + column + ".schema.json";
        Path path = Path.of(schemaDir, fileName);
        if (java.nio.file.Files.exists(path)) {
            JsonCompare.ColumnRule rule = columnRuleCache.get(path.toString());
            if (rule == null) {
                rule = jsonCompare.loadColumnRule(path);
                columnRuleCache.put(path.toString(), rule);
            }
            schema.rules.put(column, rule);
            // log("SCHEMA: loaded column schema " + fileName);
        } else {
            // log("SCHEMA: column schema not found for " + column + " (expected " + fileName + ")");
        }
    }
}

    private List<ExpectedTable> loadExpectedTables(Set<String> payloadEventIds, Set<String> payloadOrderIds) throws Exception {
        List<ExpectedTable> tables = new ArrayList<>();
        Path expectedDir = Path.of(expectedPath).getParent();
        if (expectedDir == null) {
            throw new IllegalArgumentException("Expected directory not found for " + expectedPath);
        }
        try (java.util.stream.Stream<java.nio.file.Path> stream = java.nio.file.Files.list(expectedDir)) {
            List<Path> files = stream
                    .filter(p -> p.getFileName().toString().endsWith("_expected_data.json"))
                    .toList();
            for (Path p : files) {
                String file = p.getFileName().toString();
                String tableName = file.substring(0, file.indexOf("_expected_data.json"));
                JsonNode rows = jsonCompare.loadExpected(p);
                if (!rows.isArray()) {
                    continue;
                }
                Map<String, JsonNode> expectedById = new HashMap<>();
                Map<String, JsonNode> expectedByOrder = new HashMap<>();
                for (JsonNode row : rows) {
                    String rowId = row.has("id") ? row.get("id").asText() : "";
                    String rowOrderId = row.has("orderid") ? row.get("orderid").asText() : "";
                    if (payloadEventIds.contains(rowId) || payloadOrderIds.contains(rowOrderId)) {
                        if (!rowId.isEmpty()) expectedById.put(rowId, row);
                        if (!rowOrderId.isEmpty()) expectedByOrder.put(rowOrderId, row);
                    }
                }
                JsonCompare.Schema schema = new JsonCompare.Schema();
                schema.tableName = tableName;
                tables.add(new ExpectedTable(tableName, expectedById, expectedByOrder, schema));
                // logs suppressed
            }
        }
        return tables;
    }

    private LookupConfig resolveLookup(String tableName, JsonNode expectedRow) throws Exception {
        LookupConfig cfg = new LookupConfig();
        Path lookupFile = Path.of(schemaDir, tableName + "_lookup.json");
        if (java.nio.file.Files.exists(lookupFile)) {
            JsonNode node = mapper.readTree(lookupFile.toFile());
            cfg.idColumn = node.has("idColumn") ? node.get("idColumn").asText() : null;
            cfg.orderIdColumn = node.has("orderIdColumn") ? node.get("orderIdColumn").asText() : null;
            return cfg;
        }
        if (expectedRow.has("id")) cfg.idColumn = "id";
        if (expectedRow.has("orderid")) cfg.orderIdColumn = "orderid";
        if (expectedRow.has("event_id")) cfg.idColumn = "event_id";
        if (expectedRow.has("order_id")) cfg.orderIdColumn = "order_id";
        return cfg;
    }

    private static class LookupConfig {
        String idColumn;
        String orderIdColumn;
    }

    private static class ExpectedTable {
        final String tableName;
        final Map<String, JsonNode> expectedById;
        final Map<String, JsonNode> expectedByOrder;
        final JsonCompare.Schema schema;

        ExpectedTable(String tableName, Map<String, JsonNode> expectedById, Map<String, JsonNode> expectedByOrder, JsonCompare.Schema schema) {
            this.tableName = tableName;
            this.expectedById = expectedById;
            this.expectedByOrder = expectedByOrder;
            this.schema = schema;
        }
    }

    private String writeTempPayload(JsonNode payloadNode) throws Exception {
        Path temp = Path.of("target", "payload-" + UUID.randomUUID() + ".json");
        java.nio.file.Files.createDirectories(temp.getParent());
        java.nio.file.Files.writeString(temp, mapper.writeValueAsString(payloadNode));
        return temp.toString();
    }

    private void printScenarioTableSummary(ValidationReport report) {
    for (utilities.JsonCompare.ColumnResult r : report.results) {
        if ("PASS".equals(r.status)) {
            System.out.println(r.column + " -> PASS");
            logScenario(r.column + " -> PASS");
        } else {
                System.out.println(r.column + " -> " + r.status +
                    " | expected=" + clean(r.expected) + " | actual=" + clean(r.actual));
                logScenario(r.column + " -> " + r.status +
                        " | expected=" + clean(r.expected) + " | actual=" + clean(r.actual));
        }
    }
}

    private void printFailedSummary(List<ValidationReport> reports) {
        boolean anyFail = false;
        for (ValidationReport r : reports) {
            if ("FAIL".equals(r.status)) {
                anyFail = true;
                break;
            }
        }
        if (!anyFail) {
            return;
        }
        System.out.println("Failed test cases and their respective logs");
        for (ValidationReport report : reports) {
            if (!"FAIL".equals(report.status)) {
                continue;
            }
            System.out.println("Table: " + report.tableName + " | EventId: " + report.eventId);
            for (utilities.JsonCompare.ColumnResult r : report.results) {
                if ("FAIL".equals(r.status) || "SKIPPED".equals(r.status)) {
                    System.out.println("  " + r.column + " -> " + r.status +
                            " | expected=" + clean(r.expected) + " | actual=" + clean(r.actual) + " | reason=" + r.reason);
                    logScenario("  " + r.column + " -> " + r.status +
                            " | expected=" + clean(r.expected) + " | actual=" + clean(r.actual) + " | reason=" + r.reason);
                }
            }
        }
    }

    private String clean(String s) {
        if (s == null) return null;
        return s.replace("\r", "")
                .replace("\n", "")
                .replace("\t", "")
                .trim();
    }

    private void logScenario(String msg) {
        scenarioLog.append(msg).append(System.lineSeparator());
    }

}
