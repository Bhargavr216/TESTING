package utilities;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

public class JsonCompare {
    private final ObjectMapper mapper = new ObjectMapper();
    private static final String DEFAULT_TIME_PATTERN = "^\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?$";

    public ValidationReport validateTable(
            String sourceSystem,
            String eventId,
            String tableName,
            List<Map<String, Object>> actualRows,
            JsonNode expectedArrayNode,
            Schema schema
    ) {
        ValidationReport report = new ValidationReport(sourceSystem, eventId, tableName);

        if (!expectedArrayNode.isArray()) {
            report.addGlobalError("Expected JSON must be an array for table " + tableName);
            report.setStatus("FAIL");
            return report;
        }

        int min = Math.min(expectedArrayNode.size(), actualRows.size());
        if (expectedArrayNode.size() != actualRows.size()) {
            report.addGlobalError("Row count mismatch. expected=" + expectedArrayNode.size() + " actual=" + actualRows.size());
        }

        for (int i = 0; i < min; i++) {
            JsonNode expectedRow = expectedArrayNode.get(i);
            Map<String, Object> actualRow = actualRows.get(i);
            compareRow(report, expectedRow, actualRow, schema);
        }

        report.finalizeStatus();
        return report;
    }

    private void compareRow(ValidationReport report, JsonNode expectedRow, Map<String, Object> actualRow, Schema schema) {
        System.out.println("[JsonCompare] Comparing row. Expected keys=" + expectedRow.size() + " Actual keys=" + actualRow.keySet().size());
        Iterator<String> fieldNames = expectedRow.fieldNames();
        while (fieldNames.hasNext()) {
            String field = fieldNames.next();
            JsonNode expectedValueNode = expectedRow.get(field);

            ColumnRule rule = schema.rules.getOrDefault(field, new ColumnRule());

            if (schema.isOptional(field) && !actualRow.containsKey(field)) {
                report.addSkipped(field, expectedValueNode.asText(), null, "Optional field missing in actual; skipped");
                continue;
            }

            if (schema.isRequired(field) && !actualRow.containsKey(field)) {
                report.addFailure(field, expectedValueNode.asText(), null, "Required field missing in actual");
                continue;
            }

            Object actualValueObj = actualRow.get(field);
            String actualValue = normalize(actualValueObj);
            String expectedValue = normalize(expectedValueNode.isNull() ? null : expectedValueNode.asText());

            boolean expectedIsJsonNode = expectedValueNode.isObject() || expectedValueNode.isArray();
            boolean actualLooksJson = isJsonLike(actualValue);
            boolean expectedLooksJson = isJsonLike(expectedValue);

            if ((expectedIsJsonNode || actualLooksJson || expectedLooksJson) && (rule.type == null || rule.type.isEmpty())) {
                // Auto-detect JSON columns when DB stores JSON as text
                if (isJsonSchemaEmpty(rule)) {
                    report.addFailure(field, expectedValue, actualValue, "JSON detected but no column schema found for table=" + report.tableName + ", column=" + field);
                    continue;
                }
                rule.type = "json";
            }

            if ("time".equalsIgnoreCase(rule.type)) {
                if (actualValue != null && actualValue.matches(rule.timePattern != null ? rule.timePattern : DEFAULT_TIME_PATTERN)) {
                    report.addPass(field, "TIME_FORMAT", actualValue);
                } else {
                    report.addFailure(field, "TIME_FORMAT", actualValue, "Time format invalid");
                }
                continue;
            }

            if ("json".equalsIgnoreCase(rule.type)) {
                handleJsonField(report, field, expectedValueNode, actualValue, rule);
                continue;
            }

            if (isDateTimeLike(expectedValue) || isDateTimeLike(actualValue)) {
                if (isDateTimeLike(actualValue)) {
                    report.addPass(field, expectedValue, actualValue);
                } else {
                    report.addFailure(field, expectedValue, actualValue, "Invalid datetime");
                }
                continue;
            }

            if (rule.allowed != null && !rule.allowed.isEmpty() && !rule.allowed.contains(actualValue)) {
                report.addFailure(field, expectedValue, actualValue, "Value not in allowed set");
                continue;
            }

            if (rule.notNull && (actualValue == null || actualValue.isEmpty() || "N".equalsIgnoreCase(actualValue))) {
                report.addFailure(field, expectedValue, actualValue, "Null/empty/N not allowed by schema");
                continue;
            }

            if (valuesEqual(expectedValue, actualValue)) {
                report.addPass(field, expectedValue, actualValue);
            } else {
                report.addFailure(field, expectedValue, actualValue, "Mismatch");
            }
        }
    }

    private boolean valuesEqual(String expected, String actual) {
        if (isNullLike(expected) && isNullLike(actual)) return true;
        return Objects.equals(expected, actual);
    }

    private boolean isNullLike(String v) {
        return v == null || v.isEmpty() || "N".equalsIgnoreCase(v);
    }

    private boolean isJsonLike(String v) {
        if (v == null) return false;
        String s = v.trim();
        if (s.isEmpty()) return false;
        return (s.startsWith("{") && s.endsWith("}")) || (s.startsWith("[") && s.endsWith("]"));
    }

    private boolean isJsonSchemaEmpty(ColumnRule rule) {
        if (rule == null) return true;
        boolean hasReq = rule.jsonRequiredFields != null && !rule.jsonRequiredFields.isEmpty();
        boolean hasReqPaths = rule.jsonRequiredPaths != null && !rule.jsonRequiredPaths.isEmpty();
        boolean hasOpt = rule.jsonOptionalPaths != null && !rule.jsonOptionalPaths.isEmpty();
        boolean hasIgnore = rule.jsonIgnorePaths != null && !rule.jsonIgnorePaths.isEmpty();
        return !(hasReq || hasReqPaths || hasOpt || hasIgnore);
    }

    private boolean isDateTimeLike(String v) {
        if (v == null) return false;
        String s = v.trim();
        if (s.isEmpty()) return false;
        // Accept common datetime patterns: "yyyy-MM-dd HH:mm:ss(.S)" or ISO-like "yyyy-MM-ddTHH:mm:ss(.S)(Z|+hh:mm)?"
        return s.matches("^\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}:\\d{2}(\\.\\d+)?(Z|[+-]\\d{2}:?\\d{2})?$");
    }

    private String normalize(Object v) {
        if (v == null) return null;
        return String.valueOf(v).trim();
    }

    private void handleJsonField(ValidationReport report, String field, JsonNode expectedValueNode, String actualValue, ColumnRule rule) {
        if (actualValue == null || actualValue.isEmpty()) {
            if (rule.jsonRequiredFields != null && !rule.jsonRequiredFields.isEmpty()) {
                report.addFailure(field, expectedValueNode.toString(), actualValue, "JSON field missing");
            } else {
                report.addSkipped(field, expectedValueNode.toString(), actualValue, "JSON field missing; skipped");
            }
            return;
        }

        JsonNode actualJson;
        try {
            actualJson = mapper.readTree(actualValue);
        } catch (Exception ex) {
            report.addFailure(field, expectedValueNode.toString(), actualValue, "Invalid JSON in actual");
            return;
        }

        JsonNode expectedJson = null;
        if (!expectedValueNode.isNull() && !expectedValueNode.isMissingNode()) {
            if (expectedValueNode.isTextual()) {
                try {
                    expectedJson = mapper.readTree(expectedValueNode.asText());
                } catch (Exception ex) {
                    expectedJson = expectedValueNode;
                }
            } else {
                expectedJson = expectedValueNode;
            }
        }

        if (rule.jsonRequiredFields != null) {
            for (String req : rule.jsonRequiredFields) {
                if (!jsonPathExists(actualJson, req)) {
                    report.addFailure(field + "." + req, "<required>", null, "Required JSON field missing");
                }
            }
        }
        if (rule.jsonRequiredPaths != null) {
            for (String req : rule.jsonRequiredPaths) {
                if (!jsonPathExists(actualJson, req)) {
                    report.addFailure(field + "." + req, "<required>", null, "Required JSON path missing");
                }
            }
        }

        if ("requiredOnly".equalsIgnoreCase(rule.jsonValidateMode)) {
            validateRequiredOnly(report, field, expectedValueNode, actualJson, rule);
            return;
        }

        if (expectedJson != null && expectedJson.isObject()) {
            compareJsonNodes(report, field, field, expectedJson, actualJson, rule);
        } else if (expectedJson != null && expectedJson.isArray()) {
            compareJsonNodes(report, field, field, expectedJson, actualJson, rule);
        } else if (expectedJson != null && !expectedJson.isMissingNode()) {
            if (valuesEqual(expectedJson.asText(), actualJson.asText())) {
                report.addPass(field, expectedJson.asText(), actualJson.asText());
            } else {
                report.addFailure(field, expectedJson.asText(), actualJson.asText(), "JSON value mismatch");
            }
        } else {
            report.addPass(field, "<json>", actualJson.toString());
        }
    }

    private void compareJsonNodes(ValidationReport report, String columnName, String fieldPrefix, JsonNode expected, JsonNode actual, ColumnRule rule) {
        if (expected == null) return;
        if (isIgnoredJsonPath(rule, columnName, fieldPrefix)) {
            report.addSkipped(fieldPrefix, expected.toString(), actual == null ? null : actual.toString(), "Ignored JSON path");
            return;
        }
        if (expected.isObject()) {
            Iterator<String> names = expected.fieldNames();
            while (names.hasNext()) {
                String name = names.next();
                JsonNode expChild = expected.get(name);
                JsonNode actChild = actual != null ? actual.get(name) : null;
                if (actChild == null || actChild.isMissingNode()) {
                    String fullPath = fieldPrefix + "." + name;
                    if (isRequiredJsonField(rule, columnName, fullPath, name)) {
                        report.addFailure(fullPath, expChild.toString(), null, "Missing JSON field");
                    } else {
                        report.addSkipped(fullPath, expChild.toString(), null, "Not required; missing in actual");
                    }
                    continue;
                }
                compareJsonNodes(report, columnName, fieldPrefix + "." + name, expChild, actChild, rule);
            }
        } else if (expected.isArray()) {
            int min = Math.min(expected.size(), actual != null ? actual.size() : 0);
            for (int i = 0; i < min; i++) {
                compareJsonNodes(report, columnName, fieldPrefix + "[" + i + "]", expected.get(i), actual.get(i), rule);
            }
            if (actual == null || expected.size() != actual.size()) {
                String name = lastJsonSegment(fieldPrefix);
                if (isRequiredJsonField(rule, columnName, fieldPrefix, name)) {
                    report.addFailure(fieldPrefix, "array size=" + expected.size(), actual == null ? "null" : "array size=" + actual.size(), "Array size mismatch");
                } else {
                    report.addSkipped(fieldPrefix, "array size=" + expected.size(), actual == null ? "null" : "array size=" + actual.size(), "Not required; array size mismatch");
                }
            }
        } else {
            String expVal = expected.asText();
            String actVal = actual != null ? actual.asText() : null;
            String name = lastJsonSegment(fieldPrefix);
            boolean required = isRequiredJsonField(rule, columnName, fieldPrefix, name);
            if (valuesEqual(expVal, actVal)) {
                report.addPass(fieldPrefix, expVal, actVal);
            } else if (required) {
                report.addFailure(fieldPrefix, expVal, actVal, "JSON value mismatch");
            } else {
                report.addSkipped(fieldPrefix, expVal, actVal, "Not required; mismatch skipped");
            }
        }
    }

    private boolean isRequiredJsonField(ColumnRule rule, String columnName, String fullPath, String name) {
        if (rule == null) return true;
        String relative = toRelativePath(columnName, fullPath);
        if (rule.jsonIgnorePaths != null) {
            if (rule.jsonIgnorePaths.contains(fullPath) || rule.jsonIgnorePaths.contains(relative) || rule.jsonIgnorePaths.contains(name)) {
                return false;
            }
        }
        if (rule.jsonOptionalPaths != null) {
            if (rule.jsonOptionalPaths.contains(fullPath) || rule.jsonOptionalPaths.contains(relative) || rule.jsonOptionalPaths.contains(name)) {
                return false;
            }
        }
        if (rule.jsonRequiredPaths != null && !rule.jsonRequiredPaths.isEmpty()) {
            return rule.jsonRequiredPaths.contains(fullPath) || rule.jsonRequiredPaths.contains(relative) || rule.jsonRequiredPaths.contains(name);
        }
        return true;
    }

    private boolean isIgnoredJsonPath(ColumnRule rule, String columnName, String fullPath) {
        if (rule == null || rule.jsonIgnorePaths == null) return false;
        String relative = toRelativePath(columnName, fullPath);
        return rule.jsonIgnorePaths.contains(fullPath) || rule.jsonIgnorePaths.contains(relative);
    }

    private String toRelativePath(String columnName, String fullPath) {
        String prefix = columnName + ".";
        if (fullPath.startsWith(prefix)) {
            return fullPath.substring(prefix.length());
        }
        return fullPath;
    }

    private String lastJsonSegment(String fullPath) {
        if (fullPath == null || fullPath.isEmpty()) return "";
        int dot = fullPath.lastIndexOf('.');
        if (dot >= 0 && dot < fullPath.length() - 1) {
            return fullPath.substring(dot + 1);
        }
        return fullPath;
    }

    private boolean jsonPathExists(JsonNode root, String path) {
        if (root == null || path == null || path.isEmpty()) return false;
        String[] parts = path.split("\\.");
        JsonNode current = root;
        for (String part : parts) {
            if (current == null) return false;
            int bracket = part.indexOf('[');
            if (bracket >= 0) {
                String field = part.substring(0, bracket);
                if (!field.isEmpty()) {
                    current = current.get(field);
                }
                while (bracket >= 0) {
                    int end = part.indexOf(']', bracket);
                    if (end < 0) return false;
                    String idxStr = part.substring(bracket + 1, end);
                    int idx = Integer.parseInt(idxStr);
                    if (current == null || !current.isArray() || idx >= current.size()) return false;
                    current = current.get(idx);
                    bracket = part.indexOf('[', end + 1);
                }
            } else {
                current = current.get(part);
            }
        }
        return current != null && !current.isMissingNode();
    }

    private void validateRequiredOnly(ValidationReport report, String field, JsonNode expectedValueNode, JsonNode actualJson, ColumnRule rule) {
        JsonNode expectedJson = expectedValueNode;
        if (expectedValueNode != null && expectedValueNode.isTextual()) {
            try {
                expectedJson = mapper.readTree(expectedValueNode.asText());
            } catch (Exception ignored) {
                expectedJson = expectedValueNode;
            }
        }

        List<String> required = new ArrayList<>();
        if (rule.jsonRequiredPaths != null) required.addAll(rule.jsonRequiredPaths);
        if (rule.jsonRequiredFields != null) required.addAll(rule.jsonRequiredFields);

        for (String req : required) {
            JsonNode expectedNode = getJsonPath(expectedJson, req);
            JsonNode actualNode = getJsonPath(actualJson, req);
            if (actualNode == null || actualNode.isMissingNode()) {
                report.addFailure(field + "." + req, expectedNode == null ? "<required>" : expectedNode.toString(), null, "Required JSON path missing");
                continue;
            }
            if (expectedNode != null && !expectedNode.isMissingNode()) {
                String expVal = expectedNode.asText();
                String actVal = actualNode.asText();
                if (valuesEqual(expVal, actVal)) {
                    report.addPass(field + "." + req, expVal, actVal);
                } else {
                    report.addFailure(field + "." + req, expVal, actVal, "JSON value mismatch");
                }
            } else {
                report.addPass(field + "." + req, "<required>", actualNode.asText());
            }
        }
    }

    private JsonNode getJsonPath(JsonNode root, String path) {
        if (root == null || path == null || path.isEmpty()) return null;
        String[] parts = path.split("\\.");
        JsonNode current = root;
        for (String part : parts) {
            if (current == null) return null;
            int bracket = part.indexOf('[');
            if (bracket >= 0) {
                String field = part.substring(0, bracket);
                if (!field.isEmpty()) {
                    current = current.get(field);
                }
                while (bracket >= 0) {
                    int end = part.indexOf(']', bracket);
                    if (end < 0) return null;
                    String idxStr = part.substring(bracket + 1, end);
                    int idx = Integer.parseInt(idxStr);
                    if (current == null || !current.isArray() || idx >= current.size()) return null;
                    current = current.get(idx);
                    bracket = part.indexOf('[', end + 1);
                }
            } else {
                current = current.get(part);
            }
        }
        return current;
    }

    public Schema loadSchema(Path schemaPath) throws IOException {
        String json = Files.readString(schemaPath, StandardCharsets.UTF_8);
        return mapper.readValue(json, Schema.class);
    }

    public ColumnRule loadColumnRule(Path schemaPath) throws IOException {
        String json = Files.readString(schemaPath, StandardCharsets.UTF_8);
        return mapper.readValue(json, ColumnRule.class);
    }

    public JsonNode loadExpected(Path expectedPath) throws IOException {
        String json = Files.readString(expectedPath, StandardCharsets.UTF_8);
        return mapper.readTree(json);
    }

    public static class Schema {
        public String tableName;
        public List<String> requiredFields = new ArrayList<>();
        public List<String> optionalFields = new ArrayList<>();
        public Map<String, ColumnRule> rules = new HashMap<>();

        public boolean isRequired(String field) {
            return requiredFields.contains(field);
        }

        public boolean isOptional(String field) {
            return optionalFields.contains(field);
        }
    }

    public static class ColumnRule {
        public String type = "";
        public boolean notNull = false;
        public List<String> allowed = new ArrayList<>();
        public List<String> jsonRequiredFields = new ArrayList<>();
        public List<String> jsonRequiredPaths = new ArrayList<>();
        public List<String> jsonOptionalPaths = new ArrayList<>();
        public List<String> jsonIgnorePaths = new ArrayList<>();
        public String jsonValidateMode = "";
        public String timePattern = null;
    }

    public static class ValidationReport {
        public String sourceSystem;
        public String eventId;
        public String tableName;
        public String status = "PASS";
        public List<String> globalErrors = new ArrayList<>();
        public List<ColumnResult> results = new ArrayList<>();

        public ValidationReport(String sourceSystem, String eventId, String tableName) {
            this.sourceSystem = sourceSystem;
            this.eventId = eventId;
            this.tableName = tableName;
        }

        public void addGlobalError(String err) {
            globalErrors.add(err);
        }

        public void addPass(String column, String expected, String actual) {
            results.add(new ColumnResult(column, expected, actual, "PASS", null));
        }

        public void addFailure(String column, String expected, String actual, String reason) {
            status = "FAIL";
            results.add(new ColumnResult(column, expected, actual, "FAIL", reason));
        }

        public void addSkipped(String column, String expected, String actual, String reason) {
            results.add(new ColumnResult(column, expected, actual, "SKIPPED", reason));
        }

        public void setStatus(String status) {
            this.status = status;
        }

        public void finalizeStatus() {
            if (!globalErrors.isEmpty()) status = "FAIL";
            for (ColumnResult r : results) {
                if ("FAIL".equals(r.status)) {
                    status = "FAIL";
                    return;
                }
            }
        }
    }

    public static class ColumnResult {
        public String column;
        public String expected;
        public String actual;
        public String status;
        public String reason;

        public ColumnResult(String column, String expected, String actual, String status, String reason) {
            this.column = column;
            this.expected = expected;
            this.actual = actual;
            this.status = status;
            this.reason = reason;
        }
    }
}
