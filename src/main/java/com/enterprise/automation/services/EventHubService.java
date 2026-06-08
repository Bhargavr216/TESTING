package com.enterprise.automation.services;

import com.enterprise.automation.config.EnvironmentConfig;
import com.enterprise.automation.utils.ConfigLoader;
import com.enterprise.automation.utils.JsonUtils;
import com.azure.messaging.eventhubs.EventData;
import com.azure.messaging.eventhubs.EventDataBatch;
import com.azure.messaging.eventhubs.EventHubClientBuilder;
import com.azure.messaging.eventhubs.EventHubProducerClient;
import com.azure.messaging.eventhubs.models.EventHubConnectionStringProperties;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public final class EventHubService {
    private final EnvironmentConfig.EventHubConfig config;

    public EventHubService() {
        config = ConfigLoader.load().getEventHub();
    }

    public void triggerPayload(String fileName) {
        try {
            String connectionString = config.getConnectionString();
            if (connectionString == null || connectionString.isBlank()) {
                throw new IllegalStateException("Event Hub connection string is not configured");
            }
            EventHubConnectionStringProperties connectionStringProperties = EventHubConnectionStringProperties.parse(connectionString);
            if (connectionStringProperties.getEntityPath() == null || connectionStringProperties.getEntityPath().isBlank()) {
                throw new IllegalStateException("Event Hub connection string must include EntityPath");
            }
            Path payloadFile = Paths.get(config.getPayloadPath(), fileName);
            String payloadString = Files.readString(payloadFile);
            ObjectMapper mapper = JsonUtils.mapper();
            JsonNode payload = mapper.readTree(payloadString);
            try (EventHubProducerClient producerClient = new EventHubClientBuilder()
                .connectionString(connectionString)
                .buildProducerClient()) {
                EventDataBatch batch = producerClient.createBatch();
                if (!batch.tryAdd(new EventData(payloadString))) {
                    throw new IllegalStateException("Event payload is too large to fit into a single Event Hub batch");
                }
                producerClient.send(batch);
            }
            System.out.println("[EventHubService] Triggered event payload " + fileName + " with connection string " + maskConnectionString(connectionString));
            System.out.println("[EventHubService] Payload = " + mapper.writeValueAsString(payload));
        } catch (Exception ex) {
            throw new IllegalStateException("Failed to load event payload: " + fileName, ex);
        }
    }

    private String maskConnectionString(String connectionString) {
        int index = connectionString.indexOf("SharedAccessKey=");
        if (index < 0) {
            return connectionString;
        }
        int start = index + "SharedAccessKey=".length();
        String maskedPart = "*****";
        return connectionString.substring(0, start) + maskedPart;
    }
}
