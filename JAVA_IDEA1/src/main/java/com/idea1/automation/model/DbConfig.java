package com.idea1.automation.model;

public class DbConfig {
    private String host;
    private int port;
    private String database;
    private String user;
    private String password;
    private String dbConnectionString;
    private String eventHubConnectionString;
    private String eventHubName;
    private boolean enableCleanup = true;
    private boolean enableEventTrigger = true;
    private String jiraBaseUrl;
    private String jiraProjectKey;

    public String getHost() { return host; }
    public void setHost(String host) { this.host = host; }
    public int getPort() { return port; }
    public void setPort(int port) { this.port = port; }
    public String getDatabase() { return database; }
    public void setDatabase(String database) { this.database = database; }
    public String getUser() { return user; }
    public void setUser(String user) { this.user = user; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    public String getDbConnectionString() { return dbConnectionString; }
    public void setDbConnectionString(String dbConnectionString) { this.dbConnectionString = dbConnectionString; }
    public String getEventHubConnectionString() { return eventHubConnectionString; }
    public void setEventHubConnectionString(String eventHubConnectionString) { this.eventHubConnectionString = eventHubConnectionString; }
    public String getEventHubName() { return eventHubName; }
    public void setEventHubName(String eventHubName) { this.eventHubName = eventHubName; }
    public boolean isEnableCleanup() { return enableCleanup; }
    public void setEnableCleanup(boolean enableCleanup) { this.enableCleanup = enableCleanup; }
    public boolean isEnableEventTrigger() { return enableEventTrigger; }
    public void setEnableEventTrigger(boolean enableEventTrigger) { this.enableEventTrigger = enableEventTrigger; }
    public String getJiraBaseUrl() { return jiraBaseUrl; }
    public void setJiraBaseUrl(String jiraBaseUrl) { this.jiraBaseUrl = jiraBaseUrl; }
    public String getJiraProjectKey() { return jiraProjectKey; }
    public void setJiraProjectKey(String jiraProjectKey) { this.jiraProjectKey = jiraProjectKey; }
}
