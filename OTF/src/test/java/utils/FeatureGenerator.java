package utils;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class FeatureGenerator {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            throw new IllegalArgumentException("Usage: FeatureGenerator <payload.json> <output.feature>");
        }
        Path payloadPath = Path.of(args[0]);
        Path outPath = Path.of(args[1]);
        ObjectMapper mapper = new ObjectMapper();
        JsonNode root = mapper.readTree(Files.readString(payloadPath, StandardCharsets.UTF_8));
        if (!root.isArray()) {
            throw new IllegalArgumentException("Payload file must be a JSON array");
        }

        StringBuilder sb = new StringBuilder();
        sb.append("Feature: Event-driven DB validation").append(System.lineSeparator()).append(System.lineSeparator());

        for (JsonNode node : root) {
            String eventId = node.path("event-id").asText();
            String orderId = node.path("order-id").asText();
            String eventType = node.path("eventType").asText("");
            String scenarioName = "Validate event " + eventId + " order " + orderId;
            if (!eventType.isEmpty()) {
                scenarioName = scenarioName + " type " + eventType;
            }
            sb.append("  Scenario: ").append(scenarioName).append(System.lineSeparator());
            sb.append("    Given mysql host \"localhost\" port 3306 database \"job_processing_db\" user \"root\" password \"\" and payload file \"src/main/resources/payloads/event_payload.json\" and expected file \"src/main/resources/expected/job_queue_arch_expected_data.json\" and schema dir \"src/main/resources/schemas\"").append(System.lineSeparator());
            sb.append("    Then select event-id \"").append(eventId).append("\" and order-id \"").append(orderId).append("\"").append(System.lineSeparator());
            sb.append("    Then database values should match expected data").append(System.lineSeparator()).append(System.lineSeparator());
        }

        Files.createDirectories(outPath.getParent());
        Files.writeString(outPath, sb.toString(), StandardCharsets.UTF_8);
    }
}
