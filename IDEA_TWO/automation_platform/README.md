# 🚀 Enterprise Rule-Driven Automation Framework

A powerful, service-agnostic automation platform designed for end-to-end validation of complex distributed systems (FSM, MFS, FOS). This framework uses a **Rule-Driven Approach**, meaning you define *what* to validate in JSON scenarios, and the engine handles *how* to validate it across multiple databases.

---

## 🌟 Key Features

*   **Rule-Driven Engine**: Decouples validation logic from test data.
*   **Multi-Service Support**: Validates FSM (Field Service), MFS (Mobile Financial), and FOS (Fulfillment) services.
*   **Dynamic Lookup Resolution**: Automatically extracts IDs from event payloads to find related database records.
*   **Advanced Audit Validation**: Supports strict sequence checks, retry attempt counting, and exception message validation.
*   **Enterprise Reporting**: A modern, collapsible HTML dashboard with structured validation tables.
*   **Smart Multi-Table Checks**: Validate multiple tables, columns, and JSON attributes in a single concise rule.

---

## 📂 Project Structure

```text
automation_platform/
├── config/               # Database connection settings (FSM, MFS, FOS)
├── engine/               # Core Framework Logic
│   ├── validators/       # Specialized validation rules (Audit, Smart, JSON, etc.)
│   ├── runner.py         # Entry point for suite execution
│   ├── state_executor.py # Handles event triggering and rule sequencing
│   └── report_builder.py # Generates the HTML dashboard
├── reports/              # Output directory for execution results
├── scenarios/            # JSON-based test cases (Happy Path, Negative, Retry)
├── setup_db.py           # Database initialization and data seeding script
└── suite.json            # Global execution configuration
```

---

## 🛠️ Getting Started

### 1. Prerequisites
*   Python 3.8+
*   PostgreSQL installed locally
*   `psycopg2-binary` installed (`pip install psycopg2-binary`)

### 2. Database Initialization
This script creates all 3 databases, sets up the tables, and seeds them with realistic test data.
```bash
python setup_db.py
```

### 3. Running the Suite
Execute all discovered scenarios across all services.
```bash
python -m engine.runner --suite suite.json
```

### 4. Viewing Results
After execution, open the generated report in your browser:
`reports/report.html`

---

## 📖 Documentation Links
*   [Technical Flow & File Explanation](TECHNICAL_FLOW.md)
*   [Interview Preparation Q&A](INTERVIEW_PREP.md)
*   [Future Roadmap (GenAI)](FUTURE_ROADMAP.md)
*   [Test Scenario Documentation](TEST_DOCUMENTATION.md)
