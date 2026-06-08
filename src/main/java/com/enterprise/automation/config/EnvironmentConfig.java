package com.enterprise.automation.config;

import java.util.Map;

public class EnvironmentConfig {
    private ApiConfig api;
    private DatabaseConfig database;
    private EventHubConfig eventHub;

    public ApiConfig getApi() {
        return api;
    }

    public DatabaseConfig getDatabase() {
        return database;
    }

    public EventHubConfig getEventHub() {
        return eventHub;
    }

    public static class ApiConfig {
        private String baseUrl;
        private Map<String, String> defaultHeaders;

        public String getBaseUrl() {
            return baseUrl;
        }

        public Map<String, String> getDefaultHeaders() {
            return defaultHeaders;
        }
    }

    public static class DatabaseConfig {
        private String schema;
        private String connectionString;

        public String getSchema() {
            return schema;
        }

        public String getConnectionString() {
            return connectionString;
        }
    }

    public static class EventHubConfig {
        private String connectionString;
        private String payloadPath;

        public String getConnectionString() {
            return connectionString;
        }

        public String getPayloadPath() {
            return payloadPath;
        }
    }
}
