# 🎓 Interview Preparation: Enterprise Automation Framework

This document contains common interview questions and answers related to this project, explaining the core concepts behind the design.

---

## ❓ 1. High-Level Concept Questions

### **Q: What is a Rule-Driven Framework?**
**A:** A rule-driven framework separates the "Validation Logic" (Python code) from the "Validation Requirements" (JSON scenarios). Instead of writing custom code for every test, you define rules in a JSON file, and a generic engine executes them. This makes it extremely easy to scale and maintain.

### **Q: Why use JSON for Scenarios?**
**A:** JSON is a lightweight, human-readable format. It allows non-developers (like Manual Testers or Product Owners) to read and even write test scenarios without knowing how to code in Python.

### **Q: What is the "State-Based" approach in this framework?**
**A:** Distributed systems often go through different "states" (e.g., INITIALIZED → PROCESSED → FINALIZED). Our framework validates the system at each specific state. Each state can have its own set of rules (Persistence, Audit, JSON, etc.).

---

## ❓ 2. Technical Questions

### **Q: How do you handle Dynamic Data (IDs)?**
**A:** We use **Dynamic Lookup Resolution**. The framework reads an `event_payload` and a `look_up_ref` from the scenario. It extracts the ID (like `event_id`) from the payload and uses it to build SQL queries at runtime. This allows us to run the same scenario with different IDs every time.

### **Q: How do you validate Audit Sequences?**
**A:** In the `AuditRule` module, we fetch all audit rows for a specific `event_id` and sort them by `event_time ASC`. We then loop through our "Expected Sequence" list and compare it step-by-step with the actual rows from the database.

### **Q: How does the SmartRule work?**
**A:** The `SmartRule` is a "One-Stop-Shop" validator. It can check multiple tables, simple columns, and even nested JSON attributes (using dot-notation like `payload.order.id`) in a single execution. It's designed to minimize the amount of JSON code you have to write.

---

## ❓ 3. Architecture & Performance

### **Q: How do you handle Multiple Databases?**
**A:** We use a `ServiceRegistry` and a `DBFactory`. Based on the `service` name in the scenario (e.g., "FSM"), the factory loads the correct configuration from the `config/` folder and establishes a connection to the specific database (`fsm_db`, `mfs_db`, etc.).

### **Q: How do you ensure the framework is Performant?**
**A:**
1.  **Targeted Queries**: We never load a full table. Every query uses a `WHERE` clause with an index (like `event_id`).
2.  **Stateless Execution**: Each scenario run is independent, which prevents memory leaks.
3.  **Minimal Imports**: We only load the validators needed for the specific rule being executed.

---

## ❓ 4. Scenario-Based Questions

### **Q: How would you handle a Retry failure in this framework?**
**A:** I would define a `retry` scenario in JSON. The `AuditRule` would expect a specific number of `VALIDATE` operations with `exception != NULL`. If the actual audit count in the database is less than expected, the framework will return a **FAIL** with a clear message like "Retry audit count mismatch."

### **Q: How do you validate JSON payloads inside a database column?**
**A:** Our `JsonRule` (and `SmartRule`) can parse a string column as a JSON object. We then use a "Nested Path Resolver" (using dot-notation) to reach deep into the JSON structure and compare values or check for mandatory fields.
