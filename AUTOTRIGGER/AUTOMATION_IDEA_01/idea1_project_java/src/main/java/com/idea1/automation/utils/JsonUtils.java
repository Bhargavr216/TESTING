package com.idea1.automation.utils;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class JsonUtils {
    private static final ObjectMapper mapper = new ObjectMapper();

    public static <T> T loadJson(String path, Class<T> clazz) throws IOException {
        return mapper.readValue(new File(path), clazz);
    }

    public static <T> T loadJson(String path, TypeReference<T> typeReference) throws IOException {
        return mapper.readValue(new File(path), typeReference);
    }

    public static List<Map<String, Object>> loadExpectedRows(String table) throws IOException {
        String path = "expected/tables/" + table + ".json";
        return mapper.readValue(new File(path), new TypeReference<List<Map<String, Object>>>() {});
    }
}
