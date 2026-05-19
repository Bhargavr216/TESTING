# VBR - Event Hub Trigger Application

A modern web application for triggering JSON payloads to Azure Event Hub services with a beautiful, intuitive UI.

## Features

✨ **Modern UI**
- Clean, responsive design using Bootstrap 5
- Dark themed navbar with VBR branding
- Smooth animations and transitions
- Mobile-friendly layout

🎯 **Service Management**
- Support for ~10+ services
- Easy service selection from left sidebar
- Service-specific configuration

⚡ **Dual Trigger Modes**
- **Single Mode**: Trigger one payload at a time with dynamic form fields
- **Multiple Mode**: Batch trigger multiple payloads separated by commas or newlines

📝 **Dynamic Forms**
- Auto-generated forms based on JSON configuration
- Support for multiple field types:
  - Text input
  - Number input
  - Email input
  - URL input
  - Select dropdown
  - Textarea
- Configurable field labels and validation

🔄 **Event Hub Integration**
- Direct connection to Azure Event Hub
- Connection string based authentication
- Real-time payload delivery

## Project Structure

```
AutoTrigger/
├── package.json           # Node dependencies
├── config.json           # Service configuration
├── server.js             # Express backend server
└── public/
    ├── index.html        # Main HTML page
    ├── styles.css        # Custom styling
    └── app.js            # Frontend JavaScript logic
```

## Setup Instructions

### 1. Prerequisites
- Node.js (v14 or higher)
- Azure Event Hubs setup with connection string
- npm package manager

### 2. Installation

```bash
cd AutoTrigger
npm install
```

### 3. Configuration

Edit `config.json` and update each service configuration:

```json
{
  "services": [
    {
      "id": "service1",
      "name": "Service Name",
      "connectionString": "Endpoint=sb://YOUR_NAMESPACE.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=YOUR_KEY",
      "eventHubNamespace": "YOUR_NAMESPACE",
      "eventHubName": "event-hub-name",
      "eventPayload": { /* Your JSON template */ },
      "editableFields": [
        { "key": "id", "type": "TEXT", "label": "Event ID", "placeholder": "Enter Event ID", "randomValue": true },
        { "key": "data.orderId", "type": "TEXT", "label": "Order ID", "placeholder": "Enter Order ID" }
      ]
    }
    // ... more services
  ]
}
```

### 4. Start the Server

```bash
npm start
```

The application will be available at `http://localhost:3000`

For development with auto-reload:
```bash
npm run dev
```

## Usage Guide

### Single Payload Mode

1. **Select a Service**: Click on any service from the left sidebar
2. **Single Mode**: The Single radio button is selected by default
3. **Fill Form**: Complete the visible form fields
4. **Trigger**: Click the "Trigger" button to send the payload
5. **Feedback**: See success/error messages with payload details

### Multiple Payload Mode

1. **Select a Service**: Click on any service from the left sidebar
2. **Multiple Mode**: Select the "Multiple" radio button
3. **Enter Payloads**: Paste or type multiple payloads in the textarea
4. **Format Options**:
   - Comma-separated: `field1=value1,field2=value2`
   - Newline-separated:
     ```
     field1=value1,field2=value2
     field1=value3,field2=value4
     ```
5. **Trigger**: Click "Trigger" to send all payloads
6. **Feedback**: See batch results with success/failure count

### Configuration Details

#### Service Configuration

```json
{
  "id": "unique-service-id",
  "name": "Display Name",
  "eventHubName": "event-hub-name",
  "payload": {
    "eventType": "EventName",
    "field1": "default-value",
    "field2": ""
  },
  "editableFields": ["field1", "field2"],
  "fieldLabels": {
    "field1": "Field 1 Display Name",
    "field2": "Field 2 Display Name"
  },
  "fieldTypes": {
    "field1": "text",
    "field2": "number",
    "field3": "select"
  },
  "fieldOptions": {
    "field3": ["Option1", "Option2", "Option3"]
  }
}
```

#### Supported Field Types

| Type | Description | Example |
|------|-------------|---------|
| `text` | Text input | Order ID |
| `number` | Number input | Quantity, Amount |
| `email` | Email input | Recipient Email |
| `url` | URL input | Endpoint URL |
| `select` | Dropdown select | Status, Type |
| `textarea` | Multi-line text | Message, JSON |

## API Endpoints

### `GET /api/config`
Returns the complete configuration with all services.

```bash
curl http://localhost:3000/api/config
```

### `GET /api/services/:serviceId`
Returns configuration for a specific service.

```bash
curl http://localhost:3000/api/services/service1
```

### `POST /api/trigger/single`
Triggers a single payload.

```bash
curl -X POST http://localhost:3000/api/trigger/single \
  -H "Content-Type: application/json" \
  -d '{
    "serviceId": "service1",
    "payload": {
      "orderId": "12345",
      "customerId": "C001",
      "amount": 99.99
    }
  }'
```

### `POST /api/trigger/multiple`
Triggers multiple payloads.

```bash
curl -X POST http://localhost:3000/api/trigger/multiple \
  -H "Content-Type: application/json" \
  -d '{
    "serviceId": "service1",
    "payloads": [
      {"orderId": "12345", "customerId": "C001", "amount": 99.99},
      {"orderId": "12346", "customerId": "C002", "amount": 149.99}
    ]
  }'
```

### `GET /api/health`
Health check endpoint.

```bash
curl http://localhost:3000/api/health
```

## UI Components

### Navigation Bar
- VBR branding on the left
- Tools dropdown menu on the right with:
  - About
  - Settings
  - Clear Cache

### Left Sidebar
- Service list with icons
- Active service highlighting
- Smooth hover effects

### Main Content Area
- Service details display
- Trigger mode selector (Single/Multiple)
- Dynamic form generation
- Action buttons (Trigger, Reset)
- Result alerts with feedback

## Customization

### Adding New Services

1. Edit `config.json`
2. Add a new service object to the `services` array
3. Define payload template and editable fields
4. Specify field labels, types, and options
5. Restart the server

### Styling

Modify `public/styles.css` to customize colors, fonts, and layout.

Key CSS variables:
```css
--primary-color: #0d6efd;
--secondary-color: #6c757d;
--success-color: #198754;
--danger-color: #dc3545;
```

### Adding Field Types

Edit `public/app.js` in the `generateFormFields()` function to add new input types.

## Troubleshooting

### Event Hub Connection Issues
- Verify connection string in `config.json`
- Check Event Hub namespace
- Ensure correct Event Hub names in service config

### Form Not Displaying
- Check browser console for errors
- Verify `editableFields` array in service config
- Ensure field names match `fieldLabels` and `fieldTypes`

### Payloads Not Triggering
- Check server logs for errors
- Verify Event Hub client is initialized
- Check network tab in browser DevTools

## Environment Variables

Optional `.env` file:
```
PORT=3000
NODE_ENV=development
```

## Performance Tips

- Limit textarea size for multiple payloads
- Use pagination for large service lists
- Cache configuration after first load
- Consider connection pooling for high volume

## Security Notes

- Store connection strings securely (use environment variables)
- Validate all input on the server side
- Implement authentication/authorization as needed
- Use HTTPS in production
- Sanitize textarea input before processing

## Future Enhancements

- [ ] User authentication
- [ ] Payload history and replay
- [ ] Advanced filtering and search
- [ ] Scheduled triggers
- [ ] Webhook integration
- [ ] Analytics and monitoring
- [ ] Dark mode toggle
- [ ] Export/Import configurations

## Support

For issues or questions, check:
1. Browser console for client-side errors
2. Server logs for backend errors
3. Network requests in DevTools
4. Configuration syntax in `config.json`

## License

MIT

## Author

VBR Event Hub Trigger Team
