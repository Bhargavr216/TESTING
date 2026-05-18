package com.idea1.automation.genai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.Optional;

public class GenAiConfigGenerator {
    private static final String OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions";
    private static final String DEFAULT_MODEL = "gpt-4o-mini";
    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(60);
    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final HttpClient CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(20))
            .build();

    public static void main(String[] args) {
        if (args.length != 2) {
            System.err.println("Usage: java -jar automation.jar <requirements.txt> <output.json>");
            System.exit(1);
        }

        Path requirementsFile = Path.of(args[0]);
        Path outputFile = Path.of(args[1]);
        ensureReadable(requirementsFile);

        String apiKey = Optional.ofNullable(System.getenv("OPENAI_API_KEY"))
                .filter(s -> !s.isBlank())
                .orElseThrow(() -> new IllegalStateException("OPENAI_API_KEY is required to call the GenAI service."));

        String requirements;
        try {
            requirements = Files.readString(requirementsFile, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new IllegalStateException("Unable to read requirements file: " + requirementsFile, e);
        }

        String model = Optional.ofNullable(System.getenv("OPENAI_MODEL"))
                .filter(s -> !s.isBlank())
                .orElse(DEFAULT_MODEL);

        JsonNode completion;
        try {
            completion = callOpenAi(apiKey, model, requirements);
        } catch (IOException | InterruptedException e) {
            throw new IllegalStateException("Failed to reach the GenAI service: " + e.getMessage(), e);
        }

        JsonNode configuration = extractConfiguration(completion);

        try {
            Path parent = outputFile.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.writeString(outputFile,
                    MAPPER.writerWithDefaultPrettyPrinter().writeValueAsString(configuration),
                    StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new IllegalStateException("Unable to write configuration to " + outputFile, e);
        }

        System.out.println("Generated configuration: " + outputFile.toAbsolutePath());
    }

    private static JsonNode callOpenAi(String apiKey, String model, String requirements) throws IOException, InterruptedException {
        ObjectNode payload = MAPPER.createObjectNode();
        payload.put("model", model);
        payload.put("temperature", 0.2);
        payload.put("max_tokens", 600);
        ArrayNode messages = payload.putArray("messages");
        messages.addObject()
                .put("role", "system")
                .put("content", "You are a configuration engineer that transforms plaintext requirements into machine-readable JSON.");
        messages.addObject()
                .put("role", "user")
                .put("content", buildPrompt(requirements));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(OPENAI_ENDPOINT))
                .timeout(REQUEST_TIMEOUT)
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(MAPPER.writeValueAsString(payload)))
                .build();

        HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

        if (response.statusCode() >= 300) {
            throw new IOException("OpenAI returned status " + response.statusCode() + ": " + response.body());
        }

        return MAPPER.readTree(response.body());
    }

    private static String buildPrompt(String requirements) {
        return """
                Analyze the following customer requirements and produce a single JSON object that captures the configuration.
                - The JSON must be syntactically valid (no markdown, no surrounding commentary).
                - Keep keys meaningful and descriptive; include arrays when the requirement references multiple items.
                - If a requirement is ambiguous, provide a best effort structure and flag the ambiguity in the value (for example by adding a `notes` field).

                Requirements:
                %s
                """.formatted(requirements.trim());
    }

    private static JsonNode extractConfiguration(JsonNode responseBody) {
        JsonNode contentNode = responseBody.path("choices").path(0).path("message").path("content");
        if (contentNode.isMissingNode()) {
            throw new IllegalStateException("OpenAI response does not contain a completion payload.");
        }

        String content = contentNode.asText();
        String jsonFragment = normalizeJsonFragment(content);
        try {
            return MAPPER.readTree(jsonFragment);
        } catch (IOException e) {
            throw new IllegalStateException("Unable to parse JSON from GenAI reply. Response was:\n" + content, e);
        }
    }

    private static String normalizeJsonFragment(String content) {
        String trimmed = content.trim();
        if (trimmed.startsWith("```")) {
            int secondTick = trimmed.indexOf("```", 3);
            if (secondTick > 0) {
                trimmed = trimmed.substring(3, secondTick).trim();
            }
        }

        int start = trimmed.indexOf('{');
        int end = trimmed.lastIndexOf('}');
        if (start == -1 || end == -1 || end <= start) {
            throw new IllegalStateException("GenAI response did not include a JSON object:\n" + content);
        }

        return trimmed.substring(start, end + 1);
    }

    private static void ensureReadable(Path file) {
        if (!Files.exists(file) || !Files.isRegularFile(file)) {
            throw new IllegalArgumentException("Requirements file does not exist or is not a regular file: " + file);
        }
    }
}
