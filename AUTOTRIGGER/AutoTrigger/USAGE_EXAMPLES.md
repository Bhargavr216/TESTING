# VBR - Real-World Usage Examples

## Scenario 1: E-Commerce Order Batch Processing

### Objective
Test order processing by sending 100 orders with different amounts to verify system handles volume correctly.

### Steps

1. **Select Service**: "Order Processing Service"

2. **Multiple Mode Setup**
   - How many payloads?: `100`
   - Random Prefix: `E2E-TEST-`

3. **Build Table**
   - Click "Build Table" → generates 100 rows

4. **Configure Random**
   - Check "Random" for `orderId` column
   - Result: All order IDs get `E2E-TEST-{UUID}`

5. **Set Business Data**
   - For `customerId`: manually enter or leave blank
   - For `amount`: enter varying amounts
     ```
     Row 1-33: 99.99
     Row 34-66: 149.99
     Row 67-100: 199.99
     ```

6. **Preview & Trigger**
   - Click "Show Payload" to verify structure
   - Click "Trigger" to send all 100 orders

### Expected Result
✅ Event Hub receives 100 orders with:
- Random unique IDs (E2E-TEST-...)
- Different amounts ($99.99, $149.99, $199.99)
- Auto-generated timestamps
- Status shows: "100/100 payloads sent successfully"

---

## Scenario 2: User Account Creation Batch

### Objective
Create 50 test user accounts with automated IDs but manual names and emails.

### Steps

1. **Select Service**: "User Service"

2. **Multiple Mode Setup**
   - How many payloads?: `50`
   - Random Prefix: `TESTUSER-`

3. **Build Table** → 50 rows

4. **Configure Fields**
   - **userId**: Check "Random" → `TESTUSER-{UUID}`
   - **email**: Leave unchecked, manually enter:
     ```
     Row 1-10: admin@test.com
     Row 11-30: user@test.com
     Row 31-50: guest@test.com
     ```
   - **firstName**: Manually enter test names
   - **lastName**: Manually enter test names

5. **Quick Edit Tip**
   - Enter first email, then use Ctrl+C/Ctrl+V to copy down

6. **Trigger Batch** → 50 users created

### Expected Result
✅ 50 users with:
- Auto-generated IDs: `TESTUSER-a1b2c3d4...`
- Real test emails
- Test names
- Creation timestamps

---

## Scenario 3: Transaction Testing with Payment Service

### Objective
Simulate payment processing with auto-generated transaction IDs and specific payment methods.

### Steps

1. **Select Service**: "Payment Service"

2. **Setup**
   - Payloads: `75`
   - Prefix: `PAY-TX-`

3. **Build Table** → 75 rows

4. **Configure**
   - **transactionId**: Check Random → `PAY-TX-{UUID}`
   - **paymentMethod**: Leave unchecked, enter:
     - Rows 1-25: `Credit Card`
     - Rows 26-50: `Debit Card`
     - Rows 51-75: `Bank Transfer`
   - **amount**: Enter varying amounts

5. **Trigger**

### Result
✅ 75 transactions with:
- Unique transaction IDs
- Distributed payment methods
- Various amounts
- Tracking which method is used most often

---

## Scenario 4: Audit Logging with User Actions

### Objective
Generate audit logs showing different users performing different actions.

### Steps

1. **Select Service**: "Audit Service"

2. **Setup**
   - Payloads: `100`
   - Prefix: `AUDIT-`

3. **Build Table** → 100 rows

4. **Fill Columns**
   - **userId**: Check Random → `AUDIT-{UUID}`
   - **action**: Manually vary:
     ```
     Rows 1-25: CREATE
     Rows 26-50: READ
     Rows 51-75: UPDATE
     Rows 76-100: DELETE
     ```
   - **resourceType**: Repeat pattern:
     ```
     Rows 1-50: Order
     Rows 51-100: User
     ```
   - **resourceId**: Check Random → `AUDIT-{UUID}` (different random IDs per user)

5. **Preview & Trigger**

### Result
✅ Complete audit trail with:
- Tracked user actions
- Different action types
- Associated resources
- Automatic timestamps

---

## Scenario 5: Inventory Management Bulk Update

### Objective
Update inventory for 500 products with different warehouse locations and quantities.

### Steps

1. **Select Service**: "Inventory Service"

2. **Setup**
   - Payloads: `500`
   - Prefix: `PROD-`

3. **Build Table** → 500 rows

4. **Warehouse Distribution**
   - **productId**: Check Random → Auto-generate
   - **quantity**: Manually vary in patterns:
     ```
     Every 5 rows: vary from 10, 50, 100, 250, 500
     ```
   - **warehouseId**: Repeat warehouse codes:
     ```
     WH-EAST (Rows 1-125)
     WH-WEST (Rows 126-250)
     WH-SOUTH (Rows 251-375)
     WH-NORTH (Rows 376-500)
     ```

5. **Quick Pattern Fill Tip**
   - Use prefix field to track warehouse: `PROD-WH-EAST-`
   - Random generates with location context

### Result
✅ Inventory updated across 500 products in 4 warehouses

---

## Scenario 6: Email Campaign Triggering

### Objective
Send notification emails to 200 users with different templates and messages.

### Steps

1. **Select Service**: "Email Service"

2. **Setup**
   - Payloads: `200`
   - Prefix: `CAMPAIGN-`

3. **Build Table** → 200 rows

4. **Email Configuration**
   - **to**: Enter email segments:
     ```
     Rows 1-67: segment-a@company.com
     Rows 68-134: segment-b@company.com
     Rows 135-200: segment-c@company.com
     ```
   - **subject**: Vary by segment:
     ```
     Segment A: "Exclusive Offer - 20% Off"
     Segment B: "New Feature Available"
     Segment C: "Complete Your Profile"
     ```
   - **template**: Vary templates:
     ```
     Rows 1-50: Welcome
     Rows 51-100: ResetPassword
     Rows 101-150: OrderConfirmation
     Rows 151-200: Reminder
     ```

5. **Send Campaign**

### Result
✅ 200 targeted emails with:
- Segment-specific messages
- Different templates per group
- Tracked campaign metrics

---

## Scenario 7: Performance Testing with Prefix Patterns

### Objective
Load test the system with 1000 rapid transactions using meaningful prefixes.

### Steps

1. **Select Service**: "Payment Service"

2. **Maximum Load Setup**
   - Payloads: `1000`
   - Prefix: `STRESS-TEST-`

3. **Build Table** → 1000 rows

4. **Minimal Config** (for speed)
   - **transactionId**: Check Random → All auto-filled
   - **paymentMethod**: Enter once, copy down:
     ```
     "Credit Card" for all rows
     ```
   - **amount**: Enter default:
     ```
     "50.00" for all rows
     ```

5. **Send Load**

### Result
✅ Stress test completed:
- 1000 transactions sent
- Verify system handles volume
- Performance metrics collected
- Prefix `STRESS-TEST-` marks test data for cleanup

---

## Scenario 8: Advanced - Multi-service Scenario

### Objective
Simulate complete e-commerce flow: Order → Payment → Inventory → Notification

### Phase 1: Create Orders
```
Service: Order Processing Service
Payloads: 50
Prefix: ORDER-FLOW-
Random: orderId
Result: 50 orders created
```

### Phase 2: Process Payments
```
Service: Payment Service
Payloads: 50
Prefix: ORDER-FLOW-PAYMENT-
Random: transactionId
Link: Use same customerId pattern as orders
Result: 50 payments authorized
```

### Phase 3: Update Inventory
```
Service: Inventory Service
Payloads: 50
Prefix: ORDER-FLOW-INV-
Random: productId
Quantity: Vary by order value
Result: Inventory decreased for sold items
```

### Phase 4: Send Notifications
```
Service: Email Service
Payloads: 50
Prefix: ORDER-FLOW-EMAIL-
Random: (none)
Template: OrderConfirmation for all
Result: 50 order confirmation emails sent
```

### Complete Flow Result
✅ End-to-end e-commerce transaction flow tested with:
- Correlated order IDs across services
- Consistent prefix pattern for tracking
- All downstream services updated
- Full audit trail maintained

---

## Pro Tips for Power Users

### 1. Use Prefix for Categorization
```
Development: DEV-
Staging: STAG-
Production: PROD-
Performance Test: PERF-
Security Test: SEC-
```

### 2. Bulk Copy in Tables
- Click cell, press Ctrl+C
- Select range, press Ctrl+V
- Values repeat down

### 3. Pattern Recognition
- Identify repeating patterns
- Use keyboard shortcuts for efficiency
- Preview before large batch

### 4. Naming Conventions
```
E2E-ORDPROC-001-
TEST-PAYMENT-CARD-
AUDIT-DELETE-
ANALYTICS-PAGEVIEW-
```

### 5. Parallel Testing
- Open app in 2 tabs
- Run test A in Tab 1
- Run test B in Tab 2
- Compare results

### 6. Batch Segmentation
- Instead of 1000 rows once
- Send 5 batches of 200 rows
- Easier to debug
- Better server handling

### 7. Use Random Wisely
- Check Random for IDs/Keys
- Leave unchecked for business data
- Mix both for realistic scenarios

### 8. Reset Between Tests
- Click "Reset" after each test
- Clears table and form
- Prevents cross-contamination

---

## Common Patterns

### Pattern 1: Percentage Distribution
```
10% Premium Users
30% Standard Users  
60% Free Users

In 100 rows:
Rows 1-10: Premium data
Rows 11-40: Standard data
Rows 41-100: Free data
```

### Pattern 2: Time Series
```
Simulate hourly events
Every 10 rows = next hour
Update timestamp pattern
Shows time-based system behavior
```

### Pattern 3: Error Scenarios
```
90% Success
10% Failure

Rows 1-90: Valid data
Rows 91-100: Invalid/edge case data
Test error handling
```

---

## Troubleshooting Usage

### Issue: Table scrolls slowly
**Solution**: Split into 2-3 batches of 300-400 instead of 1000

### Issue: Lost unsaved data
**Solution**: Always preview before leaving the page

### Issue: Same prefix wanted for all
**Solution**: Enter prefix once, don't change it between rows

### Issue: Need different amounts per row
**Solution**: Uncheck Random for amount, manually enter each value

### Issue: Want sequential IDs not UUID
**Solution**: Leave Random unchecked, manually type: TEST-001, TEST-002, TEST-003

---

**Ready to trigger events at scale?** 🚀 Choose a scenario, build your table, and hit trigger!
