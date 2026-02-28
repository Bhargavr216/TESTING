# Test Case Documentation - Enterprise Validation Engine

This document provides details for the 9 simplified test scenarios generated across the three services (FSM, MFS, FOS). Each service has 3 scenarios: Happy Path, Negative, and Retry.

---

## 🚀 FSM (Field Service Management)

### Test Categories
| Category | Scenario ID | Description | Validation Rules |
| :--- | :--- | :--- | :--- |
| **Happy Path** | `FSM_HAPPY_PATH_001` | Successful event processing | Persistence, Column, JSON |
| **Negative** | `FSM_NEGATIVE_001` | Non-persistence validation | Persistence (NOT_PERSIST) |
| **Retry** | `FSM_RETRY_001` | Retry logic validation | Retry (count=5, state=RETRY_EXHAUSTED) |

---

## 💰 MFS (Mobile Financial Services)

### Test Categories
| Category | Scenario ID | Description | Validation Rules |
| :--- | :--- | :--- | :--- |
| **Happy Path** | `MFS_HAPPY_PATH_001` | Successful transaction | Persistence, Column, JSON |
| **Negative** | `MFS_NEGATIVE_001` | Invalid transaction | Persistence (NOT_PERSIST) |
| **Retry** | `MFS_RETRY_001` | Transaction retry | Retry (count=5, state=RETRY_EXHAUSTED) |

---

## 📦 FOS (Fulfillment & Ordering System)

### Test Categories
| Category | Scenario ID | Description | Validation Rules |
| :--- | :--- | :--- | :--- |
| **Happy Path** | `FOS_HAPPY_PATH_001` | Successful order | Persistence, Column, JSON |
| **Negative** | `FOS_NEGATIVE_001` | Failed order | Persistence (NOT_PERSIST) |
| **Retry** | `FOS_RETRY_001` | Order retry | Retry (count=5, state=RETRY_EXHAUSTED) |

---

## 🛠️ Validation Rules Explained

### 1. Persistence Rule
- **`PERSIST`**: Verifies that a record exists in the specified table for the given `lookup_key`.
- **`NOT_PERSIST`**: Verifies that NO record exists in the table for the given `lookup_key`.

### 2. Column Rule
- Verifies specific column values in a database record.
- Supports operators: `equals`, `not_equals`, `greater_than`, `less_than`, `contains`, `in_list`.

### 3. Retry Rule
- Specifically validates the `retry_count` and `state` columns in the job queue tables.
- Useful for verifying if the system is correctly tracking retries for failed operations.

### 4. JSON Rule
- Validates nested fields within a JSONB column.
- Supports dot-notation for deep path access (e.g., `payload.details.status`).

### 5. Archive Rule
- Verifies that a record has moved from a queue table to an archive table.

### 6. Custom SQL Rule
- Allows running arbitrary SQL queries to perform complex validations.
