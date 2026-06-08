package com.enterprise.automation.utils;

import com.fasterxml.jackson.databind.JsonNode;

public final class JsonPathUtils {
    private JsonPathUtils() {}

    public static String readJsonPath(JsonNode root, String jsonPath) {
        if (jsonPath.startsWith("$.")) {
            jsonPath = jsonPath.substring(2);
        }
        String[] parts = jsonPath.split("\\.");
        JsonNode current = root;
        for (String part : parts) {
            if (current == null) {
                return null;
            }
            if (part.endsWith("]") && part.contains("[")) {
                int bracket = part.indexOf('[');
                String field = part.substring(0, bracket);
                int index = Integer.parseInt(part.substring(bracket + 1, part.length() - 1));
                current = current.path(field);
                current = current.isArray() ? current.path(index) : null;
            } else {
                current = current.path(part);
            }
        }
        return current.isMissingNode() || current.isNull() ? null : current.asText();
    }
}
