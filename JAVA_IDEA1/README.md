# Idea 1 - Azure Database & Event Hub Validation Automation

This Java-based automation framework validates end-to-end data flows triggered by Azure Event Hubs into an Azure SQL Database (or PostgreSQL).

## Features

- **Sequential Execution**: Cleans database -> Triggers Event Hub -> Waits for processing -> Validates persistence.
- **Dynamic Payloads**: Supports both single object and array of payloads in `event_payloads.json`.
- **Azure Integration**: Built-in support for Azure Event Hubs and SQL Database connection strings.
- **Rich Reporting**: Azure-themed interactive HTML report with summary cards and step-by-step logs.

## Prerequisites

- **Java 17+**
- **Maven**
- **Azure SQL Database** (or PostgreSQL)
- **Azure Event Hub**

## Configuration

Update `config/db_config.json` with your Azure credentials:

```json
{
  "dbConnectionString": "jdbc:sqlserver://yourserver.database.windows.net:1433;database=yourdb;user=youruser;password=yourpassword;...",
  "eventHubConnectionString": "Endpoint=sb://yournamespace.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...",
  "eventHubName": "your_event_hub_name"
}
```

## How to Run

### 1. Build the project
```bash
mvn clean package
```

### 2. Run the automation
You can run it directly using Maven:
```bash
mvn exec:java -Dexec.mainClass="com.idea1.automation.runner.Runner"
```
Or run the generated fat-jar:
```bash
java -jar target/automation-1.0-SNAPSHOT.jar
```

## Reports
After execution, a detailed report is generated at:
`reports/idea1_report.html`
