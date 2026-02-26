package com.idea1.automation.utils;

import com.azure.messaging.eventhubs.EventData;
import com.azure.messaging.eventhubs.EventDataBatch;
import com.azure.messaging.eventhubs.EventHubClientBuilder;
import com.azure.messaging.eventhubs.EventHubProducerClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.idea1.automation.model.DbConfig;

import java.util.Collections;

public class EventHubUtils {
    private static final ObjectMapper mapper = new ObjectMapper();

    public static void triggerEvent(DbConfig config, Object payload) throws Exception {
        String connectionString = config.getEventHubConnectionString();
        String eventHubName = config.getEventHubName();

        if (connectionString == null || eventHubName == null) {
            System.err.println("Event Hub configuration missing. Skipping event trigger.");
            return;
        }

        try (EventHubProducerClient producer = new EventHubClientBuilder()
                .connectionString(connectionString, eventHubName)
                .buildProducerClient()) {

            String jsonPayload = mapper.writeValueAsString(payload);
            EventData eventData = new EventData(jsonPayload);
            
            EventDataBatch batch = producer.createBatch();
            if (batch.tryAdd(eventData)) {
                producer.send(batch);
                System.out.println("   [EVENT] Successfully triggered event to Event Hub: " + eventHubName);
            } else {
                throw new Exception("Event is too large for a single batch");
            }
        } catch (Exception e) {
            System.err.println("   [ERROR] Failed to trigger event: " + e.getMessage());
            throw e;
        }
    }
}
