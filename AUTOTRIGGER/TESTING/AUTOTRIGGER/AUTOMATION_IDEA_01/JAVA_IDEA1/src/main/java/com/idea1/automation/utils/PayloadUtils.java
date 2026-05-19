package com.idea1.automation.utils;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public class PayloadUtils {

    private static final String TIMESTAMP_PLACEHOLDER = "{{CURRENT_TIMESTAMP_ISO}}";

    /**
     * Recursively processes a payload object (Map or List) to replace placeholders.
     * @param payload The payload object to process in-place.
     */
    @SuppressWarnings("unchecked")
    public static void processPlaceholders(Object payload) {
        if (payload instanceof Map) {
            processMap((Map<String, Object>) payload);
        } else if (payload instanceof List) {
            processList((List<Object>) payload);
        }
    }

    private static void processMap(Map<String, Object> map) {
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof String) {
                if (TIMESTAMP_PLACEHOLDER.equals(value)) {
                    // Replace placeholder with current ISO-8601 timestamp
                    entry.setValue(Instant.now().toString());
                }
            } else {
                // Recurse for nested maps or lists
                processPlaceholders(value);
            }
        }
    }

    private static void processList(List<Object> list) {
        for (int i = 0; i < list.size(); i++) {
            Object item = list.get(i);
            if (item instanceof String) {
                if (TIMESTAMP_PLACEHOLDER.equals(item)) {
                    // Replace placeholder with current ISO-8601 timestamp
                    list.set(i, Instant.now().toString());
                }
            } else {
                // Recurse for nested maps or lists
                processPlaceholders(item);
            }
        }
    }
}
