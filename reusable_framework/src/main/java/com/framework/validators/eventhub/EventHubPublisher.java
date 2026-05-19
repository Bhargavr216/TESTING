package com.framework.validators.eventhub;

import com.azure.messaging.eventhubs.*;
import com.framework.config.Config;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.nio.charset.StandardCharsets;

/**
 * Publishes events to Azure Event Hub.
 *
 * Config keys (application-{env}.properties):
 *   eventhub.connectionString = Endpoint=sb://...
 *   eventhub.name             = my-hub-name
 */
public class EventHubPublisher {

    private static final Logger log = LoggerFactory.getLogger(EventHubPublisher.class);
    private EventHubProducerClient producer;

    public void connect() {
        producer = new EventHubClientBuilder()
            .connectionString(Config.get("eventhub.connectionString"), Config.get("eventhub.name"))
            .buildProducerClient();
        log.info("[EventHub] Connected to: {}", Config.get("eventhub.name"));
    }

    /**
     * Sends a JSON payload file to the event hub.
     *
     * @param eventId     unique ID — matches the DB "id" column
     * @param eventType   event type (e.g. ORDER_CREATED)
     * @param payloadFile classpath path (e.g. testdata/payloads/order_001.json)
     */
    public void send(String eventId, String eventType, String payloadFile) throws Exception {
        String body = load(payloadFile);
        EventData event = new EventData(body);
        event.getProperties().put("id",        eventId);
        event.getProperties().put("eventType", eventType);
        event.getProperties().put("timestamp", java.time.Instant.now().toString());
        EventDataBatch batch = producer.createBatch();
        if (!batch.tryAdd(event)) throw new RuntimeException("Payload too large: " + payloadFile);
        producer.send(batch);
        log.info("[EventHub] Sent id=[{}] type=[{}]", eventId, eventType);
    }

    public void close() {
        if (producer != null) { producer.close(); log.info("[EventHub] Closed."); }
    }

    private String load(String path) throws IOException {
        try (InputStream is = getClass().getClassLoader().getResourceAsStream(path)) {
            if (is == null) throw new IOException("File not found: " + path);
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
}
