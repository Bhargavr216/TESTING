# Quick Start Guide - VBR Event Hub Trigger

## Step 1: Install Dependencies

```powershell
cd c:\Users\bharg\Desktop\TMP\WORK\AutoTrigger
npm install
```

## Step 2: Update Configuration

Edit `config.json` and update each service with your Azure Event Hub details:

```json
{
  "services": [
    {
      "id": "service1",
      "name": "Service Name",
      "connectionString": "Endpoint=sb://YOUR_NAMESPACE.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=YOUR_KEY",
      "eventHubNamespace": "YOUR_NAMESPACE",
      "eventHubName": "event-hub-name",
      "eventPayload": {
        "eventType": "SampleEvent",
        "id": "",
        "data": { "orderId": "" }
      },
      "editableFields": [
        { "key": "data.orderId", "type": "TEXT", "label": "Order ID", "placeholder": "Enter Order ID" },
        { "key": "id", "type": "TEXT", "label": "Event ID", "placeholder": "Enter Event ID", "randomValue": true }
      ]
    }
  ]
}
```

## Step 3: Run the Server

```powershell
npm start
```

You should see:

```
Event Hub Trigger Server running on http://localhost:3000
Configuration loaded: X services
```

## Step 4: Open in Browser

Navigate to: `http://localhost:3000`

## Step 5: Trigger a Payload

1. Select a service from the left sidebar
2. Fill the form fields
3. (Optional) Turn on `Random UUID` for fields that support it
4. Click `Trigger`

