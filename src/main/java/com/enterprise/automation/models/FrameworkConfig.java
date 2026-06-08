package com.enterprise.automation.models;

import java.util.Map;

public class FrameworkConfig {
    private String environmentName;
    private Api api;
    private Database database;
    private EventHub eventHub;
    private Blob blob;
    private Timeouts timeouts;
    private Reporting reporting;

    public String getEnvironmentName() {
        return environmentName;
    }

    public Api getApi() {
        return api;
    }

    public Database getDatabase() {
        return database;
    }

    public EventHub getEventHub() {
        return eventHub;
    }

    public Blob getBlob() {
        return blob;
    }

    public Timeouts getTimeouts() {
        return timeouts;
    }

    public Reporting getReporting() {
        return reporting;
    }

    public static class Api {
        private String baseUrl;
        private Map<String, String> defaultHeaders;

        public String getBaseUrl() {
            return baseUrl;
        }

        public Map<String, String> getDefaultHeaders() {
            return defaultHeaders;
        }
    }

    public static class Database {
        private String schema;
        private String connectionString;

        public String getSchema() {
            return schema;
        }

        public String getConnectionString() {
            return connectionString;
        }
    }

    public static class EventHub {
        private String connectionString;
        private String eventHubName;

        public String getConnectionString() {
            return connectionString;
        }

        public String getEventHubName() {
            return eventHubName;
        }
    }

    public static class Blob {
        private String connectionString;

        public String getConnectionString() {
            return connectionString;
        }
    }

    public static class Timeouts {
        private long pollTimeoutSeconds = 60;
        private long pollIntervalMillis = 500;

        public long getPollTimeoutSeconds() {
            return pollTimeoutSeconds;
        }

        public long getPollIntervalMillis() {
            return pollIntervalMillis;
        }
    }

    public static class Reporting {
        private String reportDir = "target/extent-report";

        public String getReportDir() {
            return reportDir;
        }
    }
}
