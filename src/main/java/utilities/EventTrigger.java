package utilities;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class EventTrigger {
    public String azureEventTrigger(String connectionString, String payloadPath) throws IOException, InterruptedException {
        String payload = Files.readString(Paths.get(payloadPath), StandardCharsets.UTF_8);
        String endpoint = extractEndpoint(connectionString);

        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(endpoint))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return response.body();
    }

    private String extractEndpoint(String connectionString) {
        if (connectionString.startsWith("http")) {
            return connectionString;
        }
        Pattern p = Pattern.compile("Endpoint=([^;]+)");
        Matcher m = p.matcher(connectionString);
        if (m.find()) {
            return m.group(1);
        }
        throw new IllegalArgumentException("Unsupported connection string format for endpoint.");
    }
}
