package com.idea1.automation.utils;

import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

class PayloadUtilsTest {

    @Test
    void placeholderReplacedInNestedStructures() {
        Map<String, Object> payload = new HashMap<>();
        payload.put("createdAt", "{{CURRENT_TIMESTAMP_ISO}}");

        Map<String, Object> nested = new HashMap<>();
        List<Object> metadata = new ArrayList<>();
        metadata.add("value");
        metadata.add("{{CURRENT_TIMESTAMP_ISO}}");
        nested.put("metadata", metadata);
        payload.put("child", nested);

        PayloadUtils.processPlaceholders(payload);

        assertNotEquals("{{CURRENT_TIMESTAMP_ISO}}", payload.get("createdAt"));
        Instant.parse(payload.get("createdAt").toString());

        Map<?, ?> child = (Map<?, ?>) payload.get("child");
        List<?> processedMetadata = (List<?>) child.get("metadata");
        assertEquals("value", processedMetadata.get(0));

        String timestampValue = processedMetadata.get(1).toString();
        assertNotEquals("{{CURRENT_TIMESTAMP_ISO}}", timestampValue);
        Instant.parse(timestampValue);
    }
}
