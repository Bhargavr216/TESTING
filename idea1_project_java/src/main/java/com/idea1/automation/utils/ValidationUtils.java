package com.idea1.automation.utils;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.idea1.automation.model.EventPayload;
import com.idea1.automation.model.TableSchema;

import java.util.*;

public class ValidationUtils {
    private static final ObjectMapper mapper = new ObjectMapper();

    public static boolean validateTablePersistence(List<Map<String, Object>> rows, String expectation) {
        if ("NOT_PERSIST".equals(expectation)) {
            return rows.isEmpty();
        }
        if ("PERSIST".equals(expectation)) {
            return !rows.isEmpty();
        }
        return true;
    }

    public static Map<String, Object> matchExpectedRow(Map<String, Object> actual, List<Map<String, Object>> expectedRows, TableSchema schema) {
        String pk = schema.getPrimary_lookup();
        String sk = schema.getSecondary_lookup();

        for (Map<String, Object> exp : expectedRows) {
            if (!Objects.equals(exp.get(pk), actual.get(pk))) {
                continue;
            }
            if (sk != null) {
                if (Objects.equals(exp.get(sk), actual.get(sk))) {
                    return exp;
                }
            } else {
                return exp;
            }
        }
        return null;
    }

    public static List<Map<String, Object>> deepCompare(JsonNode expected, JsonNode actual, String path) {
        List<Map<String, Object>> errors = new ArrayList<>();
        if (expected.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> fields = expected.fields();
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> field = fields.next();
                String k = field.getKey();
                String p = path.isEmpty() ? k : path + "." + k;
                if (!actual.has(k)) {
                    Map<String, Object> error = new HashMap<>();
                    error.put("path", p);
                    error.put("expected", field.getValue());
                    error.put("actual", null);
                    errors.add(error);
                } else {
                    errors.addAll(deepCompare(field.getValue(), actual.get(k), p));
                }
            }
        } else if (expected.isArray()) {
            for (int i = 0; i < expected.size(); i++) {
                if (i < actual.size()) {
                    errors.addAll(deepCompare(expected.get(i), actual.get(i), path + "[" + i + "]"));
                }
            }
        } else {
            if (!expected.equals(actual)) {
                Map<String, Object> error = new HashMap<>();
                error.put("path", path);
                error.put("expected", expected);
                error.put("actual", actual);
                errors.add(error);
            }
        }
        return errors;
    }

    public static void removeIgnoredPaths(JsonNode data, List<String> ignored) {
        if (data == null || !data.isObject() || ignored == null) return;
        ObjectNode objectNode = (ObjectNode) data;
        for (String path : ignored) {
            String[] keys = path.split("\\.");
            ObjectNode ref = objectNode;
            for (int i = 0; i < keys.length - 1; i++) {
                JsonNode next = ref.get(keys[i]);
                if (next != null && next.isObject()) {
                    ref = (ObjectNode) next;
                } else {
                    ref = null;
                    break;
                }
            }
            if (ref != null) {
                ref.remove(keys[keys.length - 1]);
            }
        }
    }

    public static List<String> checkRequiredJsonPaths(JsonNode data, List<String> requiredPaths) {
        List<String> missing = new ArrayList<>();
        if (data == null || requiredPaths == null) return missing;
        for (String path : requiredPaths) {
            JsonNode ref = data;
            for (String key : path.split("\\.")) {
                if (ref == null || !ref.isObject() || !ref.has(key)) {
                    missing.add(path);
                    ref = null;
                    break;
                }
                ref = ref.get(key);
            }
        }
        return missing;
    }

    public static List<Map<String, Object>> validateUniqueConstraints(List<Map<String, Object>> rows, List<List<String>> constraints) {
        List<Map<String, Object>> duplicates = new ArrayList<>();
        if (constraints == null) return duplicates;

        Map<List<String>, Set<List<Object>>> seen = new HashMap<>();

        for (Map<String, Object> row : rows) {
            for (List<String> constraint : constraints) {
                List<Object> values = new ArrayList<>();
                for (String col : constraint) {
                    values.add(row.get(col));
                }

                seen.putIfAbsent(constraint, new HashSet<>());
                if (!seen.get(constraint).add(values)) {
                    Map<String, Object> dup = new HashMap<>();
                    dup.put("constraint", constraint);
                    dup.put("key", values);
                    duplicates.add(dup);
                }
            }
        }
        return duplicates;
    }

    public static List<Map<String, Object>> validateRetryExpectations(List<Map<String, Object>> rows, String lookupCol, Object lookupValue, List<EventPayload.RetryExpectation> rules, String operationColumn) {
        List<Map<String, Object>> errors = new ArrayList<>();
        if (rules == null) return errors;

        for (EventPayload.RetryExpectation rule : rules) {
            String op = rule.getOperation();
            int expectedCount = rule.getCount();
            
            long actualCount = rows.stream()
                    .filter(r -> Objects.equals(r.get(operationColumn), op))
                    .count();

            if (actualCount != expectedCount) {
                Map<String, Object> error = new HashMap<>();
                error.put("operation", op);
                error.put("expected", expectedCount);
                error.put("actual", (int) actualCount);
                error.put("lookup", lookupCol + "=" + lookupValue);
                errors.add(error);
            }
        }
        return errors;
    }

    public static Object normalizeNullable(Object value) {
        if (value == null) return null;
        if (value instanceof String) {
            String s = ((String) value).trim().toLowerCase();
            if (s.equals("null") || s.equals("none") || s.isEmpty()) {
                return null;
            }
        }
        return value;
    }

    public static boolean compareValues(Object expected, Object actual) {
        if (expected == null && actual == null) return true;
        if (expected == null || actual == null) return false;

        // Semantic normalization
        expected = normalizeNullable(expected);
        actual = normalizeNullable(actual);

        if (expected == null && actual == null) return true;
        if (expected == null || actual == null) return false;

        if (isNumeric(expected) && isNumeric(actual)) {
            java.math.BigDecimal b1 = toBigDecimal(expected);
            java.math.BigDecimal b2 = toBigDecimal(actual);
            return b1.compareTo(b2) == 0;
        }

        return Objects.equals(expected, actual);
    }

    private static boolean isNumeric(Object obj) {
        return obj instanceof Number;
    }

    private static java.math.BigDecimal toBigDecimal(Object obj) {
        if (obj instanceof java.math.BigDecimal) return (java.math.BigDecimal) obj;
        return new java.math.BigDecimal(obj.toString());
    }
}
