# VBR Multiple Mode - Table Based Triggering Guide

## Overview

The Multiple Mode now features an advanced table-based interface for batch triggering payloads with random value generation using prefixes.

## How to Use Multiple Mode

### Step 1: Select a Service
Click on any service from the left sidebar (e.g., "Order Processing Service")

### Step 2: Switch to Multiple Mode
Click the **Multiple** radio button in the "Trigger Mode" section.

### Step 3: Configure Batch Settings

#### How Many Payloads?
- Enter the number of payloads you want to trigger (1-1000)
- Example: `100`

#### Random Prefix
- Enter a prefix that will be used when generating random values
- This prefix will be prepended to random UUIDs
- Examples:
  - `Event-ST-` → generates `Event-ST-a1b2c3d4...`
  - `ORD-` → generates `ORD-x9y8z7w6...`
  - Leave empty for just random UUIDs

### Step 4: Build the Table
Click the **Build Table** button to generate rows based on your configuration.

This creates a table with:
- **Rows**: One for each payload you specified
- **Columns**: One for each editable field in the service
- **Random Checkboxes**: In the header for each field

### Step 5: Configure Random Fields

For each column with random capability:

1. **Check the "Random" checkbox** in the column header
   - All values in that column are auto-filled with random data
   - Values become read-only (grayed out)
   
2. **Uncheck to edit manually**
   - Values become editable again
   - You can type custom values

3. **Random value types by field type**:
   - **TEXT**: `{prefix}{UUID}` → `Event-STa1b2c3d4e5f6`
   - **NUMBER**: Random integer (0-1000000)
   - **EMAIL**: `{prefix}{UUID}@example.com`
   - **URL**: `https://example.com/{prefix}{UUID}`
   - **SELECT**: Random option from dropdown list

### Step 6: Manually Edit Values

Click on any table cell to edit it:
- For text/number/email/url fields: type directly
- For select fields: choose from dropdown
- Fields with checkbox unchecked: editable, can be left blank (skipped)

### Step 7: Review Payloads

Click **Show Payload** to preview the complete payloads that will be sent before triggering.

### Step 8: Trigger Batch

Click **⚡ Trigger** to send all payloads to the Event Hub.

Success shows: `{success}/{total} payloads sent successfully`

## Examples

### Example 1: Order Processing with Prefix

1. Service: "Order Processing Service"
2. How many payloads?: `50`
3. Random Prefix: `ORD-2024-`
4. Click "Build Table"
5. Check "Random" for orderId, leave customerId and amount unedited
6. In amount column, enter: `99.99`, `149.99`, `199.99` etc
7. Click "Trigger"

Result: 50 orders sent with:
- orderId: `ORD-2024-{UUID}`
- customerId: empty (skipped)
- amount: whatever you entered

### Example 2: User Creation with Email Prefix

1. Service: "User Service"
2. How many payloads?: `100`
3. Random Prefix: `test-`
4. Click "Build Table"
5. Check "Random" for userId
6. For email: leave unchecked (will auto-generate with prefix as `test-{UUID}@example.com`)
7. For firstName/lastName: manually fill in or leave empty
8. Click "Trigger"

Result: 100 users created with random IDs and emails

## Table Features

### Sticky Header
- Column headers stay visible when scrolling down
- Field names and random checkboxes always visible

### Responsive Design
- Horizontally scrollable on smaller screens
- Table-responsive wrapper handles overflow

### Keyboard Navigation
- Tab to move between fields
- Enter to submit (on last row, if form valid)
- Shift+Tab to go back

### Form Validation
- Required fields must have values
- Type validation enforced (numbers, emails, URLs)
- Field type errors highlighted

### Auto-fill Features
- "Random" checkbox: one-click fill entire column
- Prefix: automatically prepended to all random values
- Timestamp: auto-added to payload (hidden)

## Advanced Tips

### Bulk Edit with Random
1. Enter prefix: `BATCH-001-`
2. Check "Random" for multiple fields at once
3. All selected columns fill with random values using the prefix

### Mixed Random and Manual
1. Check "Random" for technical IDs (orderId, transactionId)
2. Leave unchecked for business data (amount, name, message)
3. Manually enter business values

### Reusing Table
1. Modify table values
2. Click "Show Payload" to preview
3. Don't click "Build Table" again - this regenerates with new random values
4. Just click "Trigger" to send with current values

### Starting Over
1. Click **Clear** to empty the table
2. Click **Reset** to reset entire form back to Single mode

## Configuration for Services

For a service to support multiple mode with random values, editableFields must have `randomValue: true`:

```json
{
  "key": "data.orderId",
  "type": "TEXT",
  "label": "Order ID",
  "placeholder": "Enter Order ID",
  "randomValue": true
}
```

Edit `config.json` to enable/disable random for each field.

## Troubleshooting

### Table Not Showing
- Ensure "How many payloads?" has a value > 0
- Check browser console for errors
- Verify service has editable fields

### Random Checkbox Not Working
- Ensure field has `"randomValue": true` in config.json
- Check if field is read-only (was manually set readonly)
- Try clicking toggle again

### Values Not Saving
- Click outside the cell to ensure value is registered
- Check form validation errors at bottom

### Performance Issues with Large Batches
- For > 500 rows, table may scroll slower
- Consider splitting into multiple batches
- Close other browser tabs to free memory

## Limits

- Maximum payloads per batch: 1,000
- Maximum prefix length: 100 characters
- Field value size: depends on Event Hub limits
- Total batch size: depends on Event Hub throughput

## API Integration

The Multiple Mode sends batch data to: `POST /api/trigger/multiple`

Payload structure:
```json
{
  "serviceId": "service1",
  "payloads": [
    { "data.orderId": "ORD-2024-abc123", "data.amount": "99.99" },
    { "data.orderId": "ORD-2024-def456", "data.amount": "149.99" }
  ]
}
```
