package com.enterprise.automation.utils;

import com.enterprise.automation.services.ApiService;
import com.enterprise.automation.services.DatabaseService;
import com.enterprise.automation.services.EventHubService;

public final class ServiceContainer implements AutoCloseable {
    private final ApiService apiService = new ApiService();
    private final DatabaseService databaseService = new DatabaseService();
    private final EventHubService eventHubService = new EventHubService();

    public ApiService apiService() {
        return apiService;
    }

    public DatabaseService databaseService() {
        return databaseService;
    }

    public EventHubService eventHubService() {
        return eventHubService;
    }

    @Override
    public void close() {
        // No resources to release currently.
    }
}
