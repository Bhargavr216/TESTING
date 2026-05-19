package com.framework.validators.json;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.networknt.schema.*;
import org.assertj.core.api.Assertions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * JSON validation utility — four modes:
 *
 *  1. assertMandatoryAttributes  — check specific key-value pairs exist (ignore extras)
 *  2. assertFullMatch            — deep compare actual vs expected JSON file
 *  3. assertSchema               — validate structure against JSON Schema (Draft-07)
 *  4. extractField               — read a value from JSON string by dot-path
 */
public class JsonValidator {

    private static final Logger log = LoggerFactory.getLogger(JsonValidator.class);
    private static final ObjectMapper MAPPER = new ObjectMapper();

    // ── 1. Mandatory attributes ───────────────────────────────────

    /**
     * Checks that actual JSON contains every key-value pair in the mandatory file.
     * Extra fields in actual are ignored.
     *
     * Mandatory file format (flat JSON):
     *   { "status": "SUCCESS", "eventType": "ORDER_CREATED" }
     *
     * Supports dot-notation for nested fields: "order.customer.id"
     */
    public void assertMandatoryAttributes(String actualJson, String mandatoryFile) throws Exception {
        JsonNode actual    = parse(actualJson);
        JsonNode mandatory = loadFile(mandatoryFile);
        List<String> failures = new ArrayList<>();

        mandatory.fields().forEachRemaining(e -> {
            String expected = e.getValue().asText();
            String actual2  = nested(actual, e.getKey());
            if (actual2 == null)
                failures.add("Missing field: [" + e.getKey() + "]");
            else if (!actual2.equalsIgnoreCase(expected))
                failures.add(String.format("Field [%s]: expected=[%s] actual=[%s]", e.getKey(), expected, actual2));
            else
                log.info("[JSON] Mandatory [{}]={} ✓", e.getKey(), actual2);
        });

        if (!failures.isEmpty())
            Assertions.fail("Mandatory attribute check failed:\n  • " + String.join("\n  • ", failures));
    }

    // ── 2. Full JSON match ────────────────────────────────────────

    /**
     * Deep comparison: every field in expected file must exist in actual with same value.
     * Order doesn't matter. Extra fields in actual are OK (lenient mode).
     */
    public void assertFullMatch(String actualJson, String expectedFile) throws Exception {
        JsonNode actual   = parse(actualJson);
        JsonNode expected = loadFile(expectedFile);
        List<String> failures = new ArrayList<>();
        deepCompare("$", expected, actual, failures);
        if (!failures.isEmpty())
            Assertions.fail("Full JSON match failed:\n  • " + String.join("\n  • ", failures));
        log.info("[JSON] Full match passed ✓ [{}]", expectedFile);
    }

    // ── 3. JSON Schema ────────────────────────────────────────────

    /** Validates actual JSON against a JSON Schema (Draft-07) file. Reports all violations. */
    public void assertSchema(String actualJson, String schemaFile) throws Exception {
        JsonNode actual = parse(actualJson);
        try (InputStream is = stream(schemaFile)) {
            Set<ValidationMessage> errors = JsonSchemaFactory
                .getInstance(SpecVersion.VersionFlag.V7)
                .getSchema(is)
                .validate(actual);
            if (!errors.isEmpty()) {
                List<String> msgs = errors.stream().map(ValidationMessage::getMessage).toList();
                Assertions.fail("Schema [" + schemaFile + "] violations:\n  • " + String.join("\n  • ", msgs));
            }
            log.info("[JSON] Schema passed ✓ [{}]", schemaFile);
        }
    }

    // ── 4. Field extraction ───────────────────────────────────────

    /** Extracts a value from a JSON string using dot-notation. Returns "NULL" if missing. */
    public String extractField(String json, String dotPath) throws Exception {
        String v = nested(parse(json), dotPath);
        return v == null ? "NULL" : v;
    }

    // ── Helpers ───────────────────────────────────────────────────

    private JsonNode parse(String json) throws Exception {
        if (json == null || json.isBlank() || json.equalsIgnoreCase("NULL"))
            throw new AssertionError("Expected non-empty JSON but got: [" + json + "]");
        return MAPPER.readTree(json);
    }

    private JsonNode loadFile(String path) throws Exception {
        try (InputStream is = stream(path)) {
            return MAPPER.readTree(new String(is.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    private InputStream stream(String path) throws IOException {
        InputStream is = getClass().getClassLoader().getResourceAsStream(path);
        if (is == null) throw new IOException("File not found on classpath: " + path);
        return is;
    }

    private String nested(JsonNode root, String dotPath) {
        JsonNode n = root;
        for (String p : dotPath.split("\\.")) {
            if (n == null || !n.has(p)) return null;
            n = n.get(p);
        }
        return n == null ? null : n.asText();
    }

    private void deepCompare(String path, JsonNode exp, JsonNode act, List<String> failures) {
        if (exp.isObject()) {
            exp.fields().forEachRemaining(e -> {
                String child = path + "." + e.getKey();
                if (!act.has(e.getKey())) failures.add("Missing field: " + child);
                else deepCompare(child, e.getValue(), act.get(e.getKey()), failures);
            });
        } else if (exp.isArray()) {
            if (!act.isArray()) { failures.add("Expected array at: " + path); return; }
            if (exp.size() != act.size()) {
                failures.add("Array size at " + path + ": expected=" + exp.size() + " actual=" + act.size());
                return;
            }
            for (int i = 0; i < exp.size(); i++)
                deepCompare(path + "[" + i + "]", exp.get(i), act.get(i), failures);
        } else {
            if (!exp.asText().equalsIgnoreCase(act.asText()))
                failures.add(String.format("Value at %s: expected=[%s] actual=[%s]", path, exp.asText(), act.asText()));
        }
    }
}
