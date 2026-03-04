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

    public static int findMatch(Map<String, Object> expected, List<Map<String, Object>> actualRows, Set<Integer> usedIndices, TableSchema schema) {
        String pk = schema.getPrimary_lookup();
        String sk = schema.getSecondary_lookup();

        for (int i = 0; i < actualRows.size(); i++) {
            if (usedIndices.contains(i)) continue;
            Map<String, Object> actual = actualRows.get(i);
            
            Object expPk = normalizeNullable(expected.get(pk));
            Object actPk = normalizeNullable(actual.get(pk));
            
            if (Objects.equals(expPk, actPk)) {
                if (sk == null) return i;
                
                Object expSk = normalizeNullable(expected.get(sk));
                Object actSk = normalizeNullable(actual.get(sk));
                if (Objects.equals(expSk, actSk)) {
                    return i;
                }
            }
        }
        return -1;
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

    /**
     * Extracts a nested value from a JSON object (can be Map or JsonNode).
     * Handles string-encoded JSON and traversal through objects and arrays.
     */
    public static Object getNestedValue(Object obj, String path) {
        if (obj == null || path == null || path.isEmpty()) return obj;
        
        try {
            JsonNode node = mapper.valueToTree(obj);
            String[] keys = path.split("\\.");
            for (String key : keys) {
                node = traverse(node, key);
                if (node == null) return null;
            }
            if (node == null || node.isNull()) return null;
            if (node.isTextual()) return node.asText();
            if (node.isNumber()) return node.numberValue();
            if (node.isBoolean()) return node.asBoolean();
            return node;
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * Helper to traverse a single level. 
     * Handles:
     * 1. Parsing string-encoded JSON
     * 2. Object property access
     * 3. Array index access (if key is numeric)
     * 4. Implicit first element access (if node is array but key is not numeric)
     */
    private static JsonNode traverse(JsonNode node, String key) {
        if (node == null) return null;

        // 1. If it's a string that might be JSON, try to parse it
        if (node.isTextual()) {
            String text = node.asText().trim();
            if ((text.startsWith("{") && text.endsWith("}")) || (text.startsWith("[") && text.endsWith("]"))) {
                try {
                    node = mapper.readTree(text);
                } catch (Exception ignored) {
                    // Not valid JSON, continue as TextNode
                }
            }
        }

        // 2. Handle Object access
        if (node.isObject()) {
            return node.has(key) ? node.get(key) : null;
        }

        // 3. Handle Array access
        if (node.isArray()) {
            // Try numeric index first
            try {
                int index = Integer.parseInt(key);
                if (index >= 0 && index < node.size()) {
                    return node.get(index);
                }
            } catch (NumberFormatException e) {
                // Not a numeric index, try accessing the first element implicitly
                if (node.size() > 0) {
                    JsonNode first = node.get(0);
                    if (first.isObject() && first.has(key)) {
                        return first.get(key);
                    }
                }
            }
        }

        return null;
    }

    public static boolean compareValues(Object expected, Object actual) {
//        if (expected == null && actual == null) return true;
//        if (expected == null || actual == null) return false;
    	return compareValues(expected,actual,false);
    }
    
    public static boolean compareValues(Object expected, Object actual,boolean presenceOnly) {
//      

        // Semantic normalization first
        expected = normalizeNullable(expected);
        actual = normalizeNullable(actual);

        if (expected == null && actual == null) return true;
        if (presenceOnly) { return (expected == null && actual==null) || (expected != null && actual!=null);}
        if (expected == null || actual == null) return false;

        if (isNumeric(expected) && isNumeric(actual)) {
            java.math.BigDecimal b1 = toBigDecimal(expected);
            java.math.BigDecimal b2 = toBigDecimal(actual);
            return b1.compareTo(b2) == 0;
        }

        return Objects.equals(expected, actual);
    }

    /**
     * Validates a JSON column by checking only required paths and ignoring specified paths.
     * @return List of errors (empty = valid, non-empty = invalid)
     */
    public static List<Map<String, Object>> validateJsonColumn(Object expectedObj, Object actualObj, 
                                                                  List<String> requiredPaths, 
                                                                  List<String> ignoredPaths) {
        List<Map<String, Object>> errors = new ArrayList<>();
        
        if (expectedObj == null && actualObj == null) return errors;
        if (expectedObj == null || actualObj == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("path", "root");
            error.put("expected", expectedObj);
            error.put("actual", actualObj);
            errors.add(error);
            return errors;
        }

        try {
            JsonNode expectedJson = mapper.valueToTree(expectedObj);
            JsonNode actualJson = mapper.valueToTree(actualObj);

            // Remove ignored paths from both
            if (ignoredPaths != null && !ignoredPaths.isEmpty()) {
                removeIgnoredPaths(expectedJson, ignoredPaths);
                removeIgnoredPaths(actualJson, ignoredPaths);
            }

            // If requiredPaths are provided, validate only those paths (presence and value)
            if (requiredPaths != null && !requiredPaths.isEmpty()) {
                for (String path : requiredPaths) {
                    String[] keys = path.split("\\.");
                    JsonNode expNode = expectedJson;
                    JsonNode actNode = actualJson;

                    // traverse expected
                    for (String k : keys) {
                        expNode = traverse(expNode, k);
                        if (expNode == null) break;
                    }

                    // traverse actual
                    for (String k : keys) {
                        actNode = traverse(actNode, k);
                        if (actNode == null) break;
                    }

                    if (actNode == null) {
                        Map<String, Object> error = new HashMap<>();
                        error.put("path", path);
                        error.put("expected", expNode != null ? expNode : "required field");
                        error.put("actual", "missing");
                        errors.add(error);
                    } else if (expNode != null) {
                        if (!expNode.equals(actNode)) {
                            Map<String, Object> error = new HashMap<>();
                            error.put("path", path);
                            error.put("expected", expNode);
                            error.put("actual", actNode);
                            errors.add(error);
                        }
                    }
                    // if expNode is null but actNode present, we only required presence so it's fine
                }
            } else {
                // No specific required paths: perform full deep compare
                errors.addAll(deepCompare(expectedJson, actualJson, ""));
            }
            
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("path", "root");
            error.put("error", e.getMessage());
            errors.add(error);
        }

        return errors;
    }

    public static Map<String, Object> validateNullPresence(Map<String, String> nullCheckConfig, Map<String, Object> actualRow) {
        Map<String, Object> result = new HashMap<>();
        result.put("passed", true);
        
        if (nullCheckConfig == null || nullCheckConfig.isEmpty()) {
            return result;
        }
        
        List<Map<String, Object>> errors = new ArrayList<>();
        
        for (Map.Entry<String, String> entry : nullCheckConfig.entrySet()) {
            String column = entry.getKey();
            String expectation = entry.getValue(); // "null" or "not_null"
            
            Object actualValue = actualRow.get(column);
            boolean isNull = actualValue == null;
            
            boolean matches = false;
            String actualDisplay;
            
            if ("null".equalsIgnoreCase(expectation)) {
                matches = isNull;
                actualDisplay = isNull ? "null" : actualValue.toString();
            } else if ("not_null".equalsIgnoreCase(expectation)) {
                matches = !isNull;
                actualDisplay = isNull ? "null" : actualValue.toString();
            } else {
                matches = true;
                actualDisplay = actualValue.toString();
            }
            
            if (!matches) {
                result.put("passed", false);
                Map<String, Object> error = new HashMap<>();
                error.put("column", column);
                error.put("expected", expectation);
                error.put("actual", actualDisplay);
                errors.add(error);
            }
        }
        
        result.put("errors", errors);
        return result;
    }

    private static boolean isNumeric(Object obj) {
        return obj instanceof Number;
    }
    private static java.math.BigDecimal toBigDecimal(Object obj) {
        if (obj instanceof java.math.BigDecimal) return (java.math.BigDecimal) obj;
        return new java.math.BigDecimal(obj.toString());
    }
}
