# Enterprise Rule-Driven Automation Framework (automation_platform)

## End-to-End Explanation
The rule-driven engine reads JSON scenarios (`scenarios/*.json`), looks up the service (FSM, MFS, FOS) in `config/`, excavates the lookup IDs from the payloads (`events/`), triggers state transitions via the `engine`, and validates the downstream persistence by comparing actual database rows against the JSON-defined rules and expected tables. Every execution streams data through `state_executor.py`, logs verdicts, and outputs a rich HTML dashboard under `reports/`. The scaffolding is intentionally service-agnostic so you can plug in new services with only configuration changes.

## Key Components and Coverage
- **`config/`**: database connection settings for FSM, MFS, and FOS plus service-specific parameters.
- **`engine/`**: core logic (`runner.py`, `state_executor.py`, `report_builder.py`) and `validators/` that enforce audit, JSON, and semantic rules.
- **`events/`**: curated payloads representing happy paths, negative cases, and retry scenarios.
- **`scenarios/`**: JSON files describing what tables/columns to assert, what race conditions to simulate, and how to correlate lookups across services.
- **`reports/`**: the collapsible HTML dashboards that explain passes/fails per scenario.
- **`setup_db.py` & `db_dump.json`**: bootstrap and seed the PostgreSQL databases so the validator can compare known data sets.

## Setup & Execution
1. Install **Python 3.8+** and **PostgreSQL** locally.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run `python setup_db.py` to create the FSM/MFS/FOS databases and seed the sample data.
4. Execute the suite: `python -m engine.runner --suite suite.json`.
5. Browse `reports/report.html` for the HTML dashboard with sidebar navigation, expand/collapse controls, and per-table failure deltas.

## Reporting & Observability
- The engine produces a modern HTML report with summary cards, expandable scenario details, and error tables.
- Logs include SQL queries executed, lookup values processed, and semantic rule IDs for failures.
- The `reports/` directory can be published as a CI artifact to keep historical runs.

## Important Interview Questions & Answers
1. **Q:** What is a rule-driven automation engine and why is it better than hard-coded assertions?  
   **A:** It decouples validation logic from code by storing expected tables/columns/JSON paths in JSON files. Changing validation for a new table only requires updating `scenarios/*.json` or `schemas`, not the Python engine.
2. **Q:** How do you validate cross-service persistence?  
   **A:** Scenarios describe multiple services (FSM, MFS, FOS) and the engine resolves lookups across them, ensuring related tables all see the expected state within a single run.
3. **Q:** How do you handle audit/log validation with retries?  
   **A:** `INTERVIEW_PREP.md` and the engine both highlight `retry_expectations` (e.g., `audit_logs` must record `VALIDATE` exactly three times) plus strict sequence checks.

## Theory Knowledge for Interviews
- **Rule-Driven Architectures:** Systems where configuration drives behavior are easier to maintain; the engine simply interprets the rules and applies the validators.
- **Service-Agnostic Validation:** Keep the same core logic while swapping out service-specific configs to support FSM, MFS, FOS without duplicating code.
- **Observability in Testing:** The HTML dashboard, logs, and reports expose which tables/columns failed and why, making debugging repeatable and transparent.

## Supporting Documents
- `TECHNICAL_FLOW.md` explains how data flows from `suite.json` → `engine` → report builder.
- `TEST_DOCUMENTATION.md` lists scenario narratives, success criteria, and failure symptoms.
- `INTERVIEW_PREP.md` contains curated Q&A around the rule-driven approach and enterprise practices.
- `FUTURE_ROADMAP.md` outlines enhancements such as GenAI-driven scenario generation.

## Troubleshooting & Tips
- If the report shows missing data for a lookup, verify the payload in `events/` and the seeded data in `db_dump.json`.
- Use `python setup_db.py --fresh` (if available) to reset the databases before running new scenarios.
- Keep the scenario JSON files formatted (linted) so the runner can parse them without errors.

## Next Steps
- Integrate the HTML report into the CI pipeline and publish the artifact for each run.
- Extend the engine for API validation or visual regression by plugging new validator modules into `engine/validators`.
