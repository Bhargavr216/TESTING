# VBR Event Hub Trigger - Configuration & Features Summary

## Recent Updates

### ✅ New Config Structure
The `config.json` now uses the exact format you specified with:

#### Per-Service Configuration
Each service has its own:
- `connectionString` - Direct Event Hub connection
- `eventHubNamespace` - Azure namespace
- `eventHubName` - Event Hub topic
- `eventPayload` - Complete payload template with nested data structure

#### Editable Fields with Random Support
```json
"editableFields": [
  {
    "key": "data.orderId",
    "type": "TEXT",
    "label": "Order ID",
    "placeholder": "Enter Order ID",
    "randomValue": true
  },
  {
    "key": "data.customerId",
    "type": "TEXT",
    "label": "Customer ID",
    "placeholder": "Enter Customer ID",
    "randomValue": false
  }
]
```

### 🎯 Features Breakdown

#### Single Mode ✨
- Form-based interface with dynamic fields
- Each field type auto-detected (TEXT, NUMBER, EMAIL, etc)
- Random UUID toggle for fields with `"randomValue": true`
- Real-time form validation
- Payload preview before sending

#### Multiple Mode (Table-Based) 🚀

**NEW: Advanced Table Interface**
1. **Batch Configuration**
   - Enter how many payloads (1-1000)
   - Set random prefix (e.g., "Event-ST-")
   - Click "Build Table"

2. **Dynamic Table Generation**
   - Rows = number of payloads
   - Columns = editable fields from config
   - Sticky headers for easy navigation
   - Responsive scroll container

3. **Random Value Generation**
   - Check "Random" checkbox in column header
   - All values in column auto-fill with random data
   - Uses prefix: `{prefix}{UUID}`
   - Field type aware (different random formats per type)
   - Uncheck to manually edit

4. **Field-Type Aware Random Values**
   - TEXT: `Event-ST-a1b2c3d4e5f6`
   - NUMBER: `567890`
   - EMAIL: `Event-ST-xyz@example.com`
   - URL: `https://example.com/Event-STuvw`
   - SELECT: Random option from dropdown list

5. **Inline Editing**
   - Click any cell to edit
   - Tab through fields
   - Type validation on-the-fly
   - Dropdown for select fields

### 🔧 Configuration Structure

#### Service Object
```json
{
  "id": "service1",
  "name": "Order Processing Service",
  "connectionString": "Endpoint=sb://YOUR_NAMESPACE.servicebus.windows.net/;...",
  "eventHubNamespace": "YOUR_NAMESPACE",
  "eventHubName": "order-events",
  "eventPayload": {
    "eventType": "OrderCreated",
    "id": "12345",
    "data": {
      "orderId": "ORD001",
      "customerId": "CUST001",
      "amount": "100.00"
    },
    "timestamp": "2024-06-01T12:00:00Z"
  },
  "editableFields": [...]
}
```

#### Editable Field Object
```json
{
  "key": "data.orderId",              // Field path (supports nested with dots)
  "type": "TEXT",                      // TEXT, NUMBER, EMAIL, URL, SELECT, TEXTAREA
  "label": "Order ID",                 // Display name
  "placeholder": "Enter Order ID",     // Input hint
  "randomValue": true,                 // Enable random UUID checkbox
  "options": ["Option1", "Option2"]    // For SELECT type
}
```

### 📊 Field Types Supported

| Type | Display | Random Generation | Example |
|------|---------|------------------|---------|
| TEXT | Text input | UUID with prefix | `Event-ST-abc123def` |
| NUMBER | Number input | Random 0-1000000 | `567890` |
| EMAIL | Email input | `prefix{UUID}@example.com` | `test-xyz123@example.com` |
| URL | URL input | `https://example.com/prefix{UUID}` | `https://example.com/test-xyz` |
| SELECT | Dropdown | Random from options | Picks random value |
| TEXTAREA | Multi-line text | UUID with prefix | `Event-ST-abc123def` |

### 💾 Payload Processing

#### Single Mode Flow
1. Fill form fields
2. Click "Trigger"
3. Fields merged with template
4. Sent to Event Hub with timestamp

#### Multiple Mode Flow
1. Build table with N rows
2. Check "Random" for auto-fill
3. Manually edit other fields
4. Click "Trigger"
5. All N payloads sent in batch

### 🔗 Deep Path Support

Fields support nested JSON paths using dot notation:

```json
"key": "data.order.details.orderId"
```

This will create nested objects in the payload:
```json
{
  "data": {
    "order": {
      "details": {
        "orderId": "VALUE"
      }
    }
  }
}
```

### 🎨 UI Improvements

#### Multiple Mode Controls
- **How many payloads?**: Number input (1-1000)
- **Random Prefix**: Text input for prefix
- **Build Table**: Generates dynamic table
- **Clear**: Empties the table
- **Show Payload**: Preview before sending
- **Trigger**: Send all payloads
- **Reset**: Return to single mode

#### Table Features
- Sticky column headers (stay visible on scroll)
- Responsive overflow container
- Inline validation
- Keyboard navigation (Tab/Shift+Tab)
- Hover effects
- Read-only fields when random enabled

### 📝 All 10 Pre-configured Services

1. **Order Processing Service**
   - Fields: orderId, customerId, amount
   - Random: orderId

2. **Payment Service**
   - Fields: transactionId, paymentMethod, amount
   - Random: transactionId

3. **Inventory Service**
   - Fields: productId, quantity, warehouseId
   - Random: productId

4. **Notification Service**
   - Fields: userId, notificationType, message
   - Random: userId

5. **User Service**
   - Fields: userId, email, firstName, lastName
   - Random: userId

6. **Analytics Service**
   - Fields: sessionId, eventName, properties
   - Random: sessionId

7. **Email Service**
   - Fields: to, subject, template
   - Random: (none)

8. **Report Service**
   - Fields: reportId, reportType, dateRange
   - Random: reportId

9. **Audit Service**
   - Fields: userId, action, resourceType, resourceId
   - Random: userId

10. **Webhook Service**
    - Fields: webhookId, endpoint, retryCount
    - Random: webhookId

### 🚀 Quick Start with New Features

```bash
# 1. Install and start
npm install
npm start

# 2. Open in browser
http://localhost:3000

# 3. Select a service (e.g., "Order Processing Service")

# 4. Try Single Mode
- Fill form fields
- Toggle Random for orderId
- Click Trigger

# 5. Try Multiple Mode
- Switch to Multiple radio button
- Enter "50" for payloads
- Enter "ORD-2024-" for prefix
- Click "Build Table"
- Check Random for orderId column
- Manually enter amounts: 99.99, 149.99, etc
- Click "Trigger"
- Result: 50 orders with random IDs, your amounts, timestamp
```

### 🔐 Security Features

- Path sanitization (prevents prototype pollution)
- Input validation
- Type checking
- Required field enforcement
- Safe nested object creation

### 📊 Performance

- Tables support up to 1,000 rows
- Batch API can handle multiple payloads
- Efficient DOM rendering
- Sticky headers don't impact scroll performance

### 🛠️ Configuration Tips

#### Enable Random for Technical IDs
```json
{
  "key": "data.orderId",
  "type": "TEXT",
  "label": "Order ID",
  "randomValue": true   // ← Will show toggle
}
```

#### Disable for Business Data
```json
{
  "key": "data.amount",
  "type": "NUMBER",
  "label": "Order Amount",
  "randomValue": false  // ← No toggle, manual entry only
}
```

#### For Select Fields
```json
{
  "key": "data.status",
  "type": "SELECT",
  "label": "Status",
  "options": ["Pending", "Processing", "Complete"],
  "randomValue": false
}
```

When random enabled, randomly picks from options.

### 📚 Documentation Files

- **README.md**: Full API and feature documentation
- **QUICKSTART.md**: 5-minute quick start
- **MULTIPLE_MODE_GUIDE.md**: Advanced table mode guide (NEW!)
- **config.json**: All services configured with randomValue support

### ✨ Next Steps

1. Update config.json with your Event Hub details
2. Run: `npm start`
3. Visit: `http://localhost:3000`
4. Try both Single and Multiple modes
5. Check MULTIPLE_MODE_GUIDE.md for advanced usage

---

**VBR v2.0** - Table-Based Batch Event Triggering with Prefix-Based Random Generation 🚀
