import json
import psycopg2
from jsonschema import validate, ValidationError
import os

PERSIST = "PERSIST"
NOT_PERSIST = "NOT_PERSIST"

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# LOGGING HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def banner(text):
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)

def section(title):
    print(f"\nTABLE : {title}")
    print("-" * 80)

def success(msg):
    print(f"   [OK] {msg}")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# DETAILED FAILURE
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def detailed_failure(table, column, expected=None, actual=None, path=None):
    print("   [FAILURE]")
    print(f"      Table   : {table}")
    print(f"      Column  : {column}")
    if path:
        print(f"      Path    : {path}")
    if expected is not None:
        print(f"      Expected: {expected}")
    if actual is not None:
        print(f"      Actual  : {actual}")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HTML HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def html_header():
    return """
<html>
<head>
<meta charset="UTF-8">
<title>Idea 1 Automation Report</title>
<style>
:root {
  --bg: #f3f7fb;
  --panel: #ffffff;
  --panel-soft: #f8fbff;
  --line: #d9e4f1;
  --text: #1f2a37;
  --muted: #5b6b80;
  --accent: #0f5cab;
  --accent-soft: #e7f1ff;
  --ok: #0f7a43;
  --ok-soft: #ddf7e8;
  --warn: #9a6600;
  --warn-soft: #fff4d6;
  --err: #b12235;
  --err-soft: #ffe6ea;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: "Manrope", "Segoe UI", Arial, sans-serif;
  background:
    radial-gradient(circle at 5% 5%, #e8f1ff 0%, transparent 32%),
    radial-gradient(circle at 95% 0%, #f0f7ff 0%, transparent 28%),
    var(--bg);
  margin: 0;
  color: var(--text);
}
h1 { margin: 0; color: #0f1a2b; font-size: 22px; letter-spacing: 0.2px; }
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--line);
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.toolbar { display: flex; gap: 8px; }
.toolbar button {
  border: 1px solid var(--line);
  background: linear-gradient(180deg, #ffffff 0%, #f6faff 100%);
  color: #0f2842;
  border-radius: 10px;
  padding: 7px 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s ease;
}
.toolbar button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(15, 92, 171, 0.12);
  border-color: #bcd3ec;
}
.layout { display: grid; grid-template-columns: 260px 1fr; gap: 16px; padding: 16px; }
.sidebar {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px;
  height: calc(100vh - 110px);
  position: sticky;
  top: 82px;
  overflow: auto;
  box-shadow: 0 10px 24px rgba(16, 38, 68, 0.07);
}
.sidebar h3 {
  margin: 0 0 12px 0;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: var(--muted);
}
.case-link {
  display: block;
  text-decoration: none;
  color: #0f2842;
  background: var(--panel-soft);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 9px 10px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.15s ease;
}
.case-link:hover {
  background: #eef5ff;
  border-color: #bfd5ef;
  transform: translateX(2px);
}
.content { min-width: 0; }
.case {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  margin-bottom: 16px;
  box-shadow: 0 10px 28px rgba(18, 40, 70, 0.08);
  overflow: hidden;
}
.case summary {
  list-style: none;
  cursor: pointer;
  padding: 14px 16px;
  background: linear-gradient(180deg, #fcfeff 0%, #f4f8fd 100%);
  border-bottom: 1px solid var(--line);
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.case summary::-webkit-details-marker { display:none; }
.case-id {
  font-weight: 800;
  color: #0f2842;
  background: #e2edf9;
  border: 1px solid #c8dbee;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
}
.case-title { font-weight: 700; color: #0f1f34; }
.case-meta { color: var(--muted); font-size: 13px; }
.case-body { padding: 14px 16px 16px 16px; }
.case-overview {
  background: linear-gradient(180deg, #f8fbff 0%, #f3f8ff 100%);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 12px;
}
.case-overview p { margin: 4px 0; }
.box {
  background: var(--panel);
  border: 1px solid var(--line);
  padding: 12px;
  margin-bottom: 12px;
  border-radius: 12px;
}
.box h3 {
  margin: 0 0 8px 0;
  color: #0f1f34;
  font-size: 15px;
}
.pass {
  color: var(--ok);
  font-weight: 600;
  background: var(--ok-soft);
  border: 1px solid #b9ebcd;
  padding: 8px 10px;
  border-radius: 8px;
}
.fail {
  color: var(--err);
  font-weight: 600;
}
.fail pre {
  margin: 0 0 8px 0;
  background: linear-gradient(180deg, #fff7f8 0%, #fff0f3 100%);
  border: 1px solid #ffc7d0;
  padding: 10px;
  border-radius: 10px;
  white-space: pre-wrap;
  line-height: 1.35;
  font-weight: 500;
}
h2, h3 { color: #0f1f34; margin-top: 0; }
.case-footer {
  border-top: 1px dashed var(--line);
  margin-top: 10px;
  padding-top: 10px;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.chip {
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 800;
  border: 1px solid transparent;
}
.chip-pass { background: var(--ok-soft); color: var(--ok); border-color: #b9ebcd; }
.chip-fail { background: var(--err-soft); color: var(--err); border-color: #ffcad2; }
.chip-skip { background: var(--warn-soft); color: var(--warn); border-color: #f2d99a; }
@media (max-width: 960px) {
  .layout { grid-template-columns:1fr; }
  .sidebar { position:relative; top:0; height:auto; }
}
</style>
<script>
function expandAllCases() {
  document.querySelectorAll('details.case').forEach(function(el) { el.open = true; });
}
function collapseAllCases() {
  document.querySelectorAll('details.case').forEach(function(el) { el.open = false; });
}
</script>
</head>
<body>
<div class="topbar">
  <h1>Idea 1 Automation Execution Report</h1>
  <div class="toolbar">
    <button type="button" onclick="expandAllCases()">Expand All</button>
    <button type="button" onclick="collapseAllCases()">Collapse All</button>
  </div>
</div>
"""

def html_footer():
    return "</main></div></body></html>"

def html_failure_block(table, column, expected=None, actual=None, path=None):
    html = "<div class='fail'><pre>"
    html += f"Table   : {table}\n"
    html += f"Column  : {column}\n"
    if path:
        html += f"Path    : {path}\n"
    if expected is not None:
        html += f"Expected: {expected}\n"
    if actual is not None:
        html += f"Actual  : {actual}\n"
    html += "</pre></div>"
    return html

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# UTILITIES
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def validate_table_persistence(rows, expectation):
    if expectation == NOT_PERSIST:
        return len(rows) == 0
    if expectation == PERSIST:
        return len(rows) > 0
    return True

def is_generated_column(schema, column):
    return column in schema.get("generated_columns", [])

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_db_connection():
    return psycopg2.connect(**load_json("config/db_config.json"))

def load_expected_rows(table):
    return load_json(f"expected/tables/{table}.json")

def normalize_nullable(value):
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in ["null", "none", ""]:
        return None
    return value

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MATCHING
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def match_expected_row(actual, expected_rows, schema):
    pk = schema["primary_lookup"]
    sk = schema.get("secondary_lookup")

    for exp in expected_rows:
        if exp.get(pk) != actual.get(pk):
            continue
        if sk:
            if exp.get(sk) == actual.get(sk):
                return exp
        else:
            return exp
    return None

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# JSON HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def remove_ignored_paths(data, ignored):
    for path in ignored:
        keys = path.split(".")
        ref = data
        for k in keys[:-1]:
            ref = ref.get(k, {})
        ref.pop(keys[-1], None)

def deep_compare(expected, actual, path=""):
    errors = []
    if isinstance(expected, dict):
        for k in expected:
            p = f"{path}.{k}" if path else k
            if k not in actual:
                errors.append({"path": p, "expected": expected[k], "actual": None})
            else:
                errors.extend(deep_compare(expected[k], actual[k], p))
    elif isinstance(expected, list):
        for i, (e, a) in enumerate(zip(expected, actual)):
            errors.extend(deep_compare(e, a, f"{path}[{i}]"))
    else:
        if expected != actual:
            errors.append({"path": path, "expected": expected, "actual": actual})
    return errors

def check_required_json_paths(actual_json, required_paths):
    missing = []
    for path in required_paths:
        ref = actual_json
        for key in path.split("."):
            if not isinstance(ref, dict) or key not in ref:
                missing.append(path)
                break
            ref = ref[key]
    return missing

# âœ… ADDITION â€” REQUIRED CHECK IN EXPECTED
def check_required_json_paths_in_expected(expected_json, required_paths):
    missing = []
    for path in required_paths:
        ref = expected_json
        for key in path.split("."):
            if not isinstance(ref, dict) or key not in ref:
                missing.append(path)
                break
            ref = ref[key]
    return missing

# âœ… ADDITION â€” UNIQUE CONSTRAINT VALIDATION
def validate_unique_constraints(rows, columns, constraints):
    seen = {}
    duplicates = []

    for row in rows:
        data = dict(zip(columns, row))

        for constraint in constraints:
            constraint_key = tuple(constraint)  # âœ… make it hashable
            value_key = tuple(data[col] for col in constraint)

            if constraint_key not in seen:
                seen[constraint_key] = set()

            if value_key in seen[constraint_key]:
                duplicates.append((constraint, value_key))
            else:
                seen[constraint_key].add(value_key)

    return duplicates

def validate_retry_expectations(rows, columns, lookup_col, lookup_value, rules, operation_column="operation"):
    errors = []
    row_dicts = [dict(zip(columns, row)) for row in rows]
    for rule in rules:
        op = rule.get("operation")
        expected_count = rule.get("count")
        if op is None or expected_count is None:
            continue
        actual_count = sum(1 for r in row_dicts if r.get(operation_column) == op)
        if actual_count != expected_count:
            errors.append({
                "operation": op,
                "expected": expected_count,
                "actual": actual_count,
                "lookup": f"{lookup_col}={lookup_value}"
            })
    return errors
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MAIN RUNNER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    payloads = load_json("payloads/event_payloads.json")
    schemas = load_json("schemas/table_schema.json")

    conn = get_db_connection()

    total_cases = total_tables = passed_tables = failed_tables = skipped_tables = 0 
    failure_summary = []

    html_report = html_header()
    html_report += """
<div class="layout">
<aside class="sidebar">
<h3>Project / Testcases</h3>
"""
    for payload in payloads:
        test_case_id = payload.get("test_case_id", "UNKNOWN")
        html_report += f'<a class="case-link" href="#case-{test_case_id}">{test_case_id}</a>'
    html_report += """
</aside>
<main class="content">
"""

    for payload in payloads:
        expected_tables = payload.get("expected_tables", [])
        table_expectations = payload.get("table_expectations", {})
        total_cases += 1
        case_failed = False
        case_passed_tables = 0
        case_skipped_tables = 0
        case_failed_tables = 0

        banner(
            f"TEST CASE : {payload['test_case_id']}\n"
            f"SCENARIO  : {payload['scenario_name']}\n"
            f"EVENT     : {payload['event_type']}\n"
            f"ORDER ID  : {payload['lookup_ids']['order_id']}"
        )

        html_report += f"""
<details class="case" id="case-{payload['test_case_id']}" open>
<summary>
  <span class="case-id">{payload['test_case_id']}</span>
  <span class="case-title">{payload['scenario_name']}</span>
  <span class="case-meta">Event: {payload['event_type']} | Order: {payload['lookup_ids']['order_id']}</span>
</summary>
<div class="case-body">
<div class="case-overview">
<p><b>Scenario:</b> {payload['scenario_name']}</p>
<p><b>Event:</b> {payload['event_type']}</p>
<p><b>Order ID:</b> {payload['lookup_ids']['order_id']}</p>
</div>
"""
        # =========================================================
        # TABLE PERSISTENCE VALIDATION (EVEN IF NOT IN expected_tables)
        # =========================================================
        expected_tables = payload.get("expected_tables", [])
        table_expectations = payload.get("table_expectations", {})

        for table, expectation in table_expectations.items():
            # Skip if this table will be fully validated later
            if table in expected_tables:
                continue

            total_tables += 1

            schema = schemas.get(table)
            if not schema:
                detailed_failure(
                    table=table,
                    column="SCHEMA",
                    expected="Schema must exist",
                    actual="Missing"
                )
                failure_summary.append(f"{table} schema missing")
                case_failed = True
                failed_tables += 1
                case_failed_tables += 1
                continue

            lookup = schema["primary_lookup"]
            lookup_value = payload["lookup_ids"][lookup]

            cur = conn.cursor()
            cur.execute(
                f"SELECT * FROM {table} WHERE {lookup}=%s",
                (lookup_value,)
            )
            rows = cur.fetchall()
            cur.close()

            is_valid = validate_table_persistence(rows, expectation)

            if not is_valid:
                html_report += f"<div class='box'><h3>Table : {table}</h3>"
                detailed_failure(
                    table=table,
                    column="ROW_PERSISTENCE",
                    expected=expectation,
                    actual=f"{len(rows)} rows found for lookup {lookup}={lookup_value}"
                )
                html_report += html_failure_block(
                    table,
                    "ROW_PERSISTENCE",
                    expectation,
                    f"{len(rows)} rows found for lookup {lookup}={lookup_value}"
                )
                html_report += "</div>"
                failure_summary.append(f"{table} persistence violation for {lookup}={lookup_value}")
                case_failed = True
                failed_tables += 1
                case_failed_tables += 1
            else:
                print(f"   [SKIPPED] {table} data validation (presence check only)")
                skipped_tables += 1
                case_skipped_tables += 1
                html_report += f"""
<div class='box'>
<h3>Table : {table}</h3>
<p class='pass'>[SKIPPED] Presence validation only ({expectation})</p>
</div>
"""
            
        for table in payload["expected_tables"]:
            total_tables += 1
            table_failed = False
            section(table)

            html_report += f"<div class='box'><h3>Table : {table}</h3>"

            schema = schemas.get(table)
            if not schema:
                detailed_failure(table, "SCHEMA", "Schema must exist", "Missing")
                continue

            lookup = schema["primary_lookup"]
            value = payload["lookup_ids"][lookup]

            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {table} WHERE {lookup}=%s", (value,))
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            cur.close()

            # Mandatory table in expected_tables must be persisted for the lookup id.
            if len(rows) == 0:
                detailed_failure(
                    table,
                    "ROW_PERSISTENCE",
                    "PERSIST (rows must exist)",
                    f"0 rows found for lookup {lookup}={value}"
                )
                html_report += html_failure_block(
                    table,
                    "ROW_PERSISTENCE",
                    "PERSIST (rows must exist)",
                    f"0 rows found for lookup {lookup}={value}"
                )
                failure_summary.append(f"{table} not persisted for {lookup}={value}")
                table_failed = True
                html_report += "</div>"
                failed_tables += 1
                case_failed = True
                case_failed_tables += 1
                continue

            retry_expectations = payload.get("retry_expectations", {})
            table_retry_rules = retry_expectations.get(table, [])
            if table_retry_rules:
                operation_col = schema.get("secondary_lookup", "operation")
                retry_errors = validate_retry_expectations(
                    rows,
                    cols,
                    lookup,
                    value,
                    table_retry_rules,
                    operation_column=operation_col
                )
                for err in retry_errors:
                    detailed_failure(
                        table,
                        "RETRY_COUNT",
                        f"{err['operation']} should repeat {err['expected']} times for {err['lookup']}",
                        f"found {err['actual']} times"
                    )
                    html_report += html_failure_block(
                        table,
                        "RETRY_COUNT",
                        f"{err['operation']} should repeat {err['expected']} times for {err['lookup']}",
                        f"found {err['actual']} times"
                    )
                    failure_summary.append(f"{table}.RETRY_COUNT.{err['operation']}")
                    table_failed = True
            # âœ… UNIQUE VALIDATION
            duplicates = validate_unique_constraints(
                rows,
                cols,
                schema.get("unique_constraints", [])
            )
            for constraint, key in duplicates:
                detailed_failure(table, "UNIQUE_CONSTRAINT", constraint, key)
                html_report += html_failure_block(table, "UNIQUE_CONSTRAINT", constraint, key)
                failure_summary.append(f"{table} unique violation {constraint}")
                table_failed = True

            expected_rows = load_expected_rows(table)

            for row in rows:
                actual = dict(zip(cols, row))
                exp = match_expected_row(actual, expected_rows, schema)
                if not exp:
                    detailed_failure(table, "ROW_MATCH", "Expected row", "Not found")
                    html_report += html_failure_block(table, "ROW_MATCH", "Expected row", "Not found")
                    failure_summary.append(f"{table}.ROW_MATCH")
                    table_failed = True
                    continue

                for col in schema["mandatory_columns"]:
                    semantic_rules = schema.get("semantic_rules", {})

                    # SEMANTIC RULE
                    if col in semantic_rules and semantic_rules[col]["type"] == "nullable_presence":
                        if normalize_nullable(exp.get(col)) != normalize_nullable(actual.get(col)):
                            detailed_failure(table, col, exp.get(col), actual.get(col))
                            html_report += html_failure_block(table, col, exp.get(col), actual.get(col))
                            failure_summary.append(f"{table}.{col}")
                            table_failed = True
                        else:
                            success(f"{col} semantic OK")
                        continue

                    # JSON COLUMN
                    if isinstance(schema.get("json_columns"), dict) and col in schema["json_columns"]:
                        cfg = schema["json_columns"][col]
                        if col not in exp:
                            detailed_failure(
                                table=table,
                                column=col,
                                expected="FIELD SHOULD BE PERSISTED IN EXPECTED FILE",
                                actual="FIELD NOT PERSISTED IN EXPECTED FILE"
                            )
                            html_report += html_failure_block(
                                table,
                                col,
                                "FIELD SHOULD BE PERSISTED IN EXPECTED FILE",
                                "FIELD NOT PERSISTED IN EXPECTED FILE"
                            )
                            failure_summary.append(f"{table}.{col} not persisted in expected file")
                            table_failed = True
                            continue
                        if actual.get(col) is None:
                            detailed_failure(table, col, "JSON VALUE", "NULL")
                            html_report += html_failure_block(table, col, "JSON VALUE", "NULL")
                            failure_summary.append(f"{table}.{col}")
                            table_failed = True
                            continue
                        actual_json = actual[col]
                        if isinstance(actual_json, str):
                            actual_json = json.loads(actual_json)
                        expected_json = exp[col]

                        for src in (actual_json, expected_json):
                            remove_ignored_paths(src, cfg.get("ignored", []))

                        required = cfg.get("required", [])

                        # REQUIRED IN ACTUAL
                        for path in check_required_json_paths(actual_json, required):
                            detailed_failure(table, col, "REQUIRED FIELD", "MISSING", path)
                            html_report += html_failure_block(table, col, "REQUIRED FIELD", "MISSING", path)
                            failure_summary.append(f"{table}.{col}.{path}")
                            table_failed = True

                        # REQUIRED IN EXPECTED
                        for path in check_required_json_paths_in_expected(expected_json, required):
                            detailed_failure(table, col, "REQUIRED IN EXPECTED", "MISSING", path)
                            html_report += html_failure_block(table, col, "REQUIRED IN EXPECTED", "MISSING", path)
                            failure_summary.append(f"{table}.{col}.{path}")
                            table_failed = True

                        for e in deep_compare(expected_json, actual_json):
                            detailed_failure(table, col, e["expected"], e["actual"], e["path"])
                            html_report += html_failure_block(table, col, e["expected"], e["actual"], e["path"])
                            failure_summary.append(f"{table}.{col}.{e['path']}")
                            table_failed = True

                        continue

                    # NORMAL COLUMN
                    # Skip value check for generated columns (e.g. audit_id)
                    if is_generated_column(schema, col):
                        if actual.get(col) is None:
                            detailed_failure(
                                table, col,
                                expected="GENERATED VALUE",
                                actual="NULL"
                            )
                            html_report += html_failure_block(
                                table, col,
                                "GENERATED VALUE",
                                "NULL"
                            )
                            failure_summary.append(f"{table}.{col}")
                            table_failed = True
                        else:
                            success(f"{col} : generated value present")
                        continue

                    # NORMAL COLUMN VALUE CHECK
                    if exp.get(col) != actual.get(col):
                        detailed_failure(table, col, exp.get(col), actual.get(col))
                        html_report += html_failure_block(table, col, exp.get(col), actual.get(col))
                        failure_summary.append(f"{table}.{col}")
                        table_failed = True
                    else:
                        success(f"{col} : {actual.get(col)}")
                        html_report += f"<p class='pass'>[OK] {col} : {actual.get(col)}</p>"

            html_report += "</div>"

            if table_failed:
                failed_tables += 1
                case_failed = True
                case_failed_tables += 1
            else:
                passed_tables += 1
                case_passed_tables += 1

        case_result_text = "PASSED"
        case_result_class = "chip-pass"
        if case_failed:
            banner("TEST CASE RESULT : FAILED")
            case_result_text = "FAILED"
            case_result_class = "chip-fail"
        elif case_skipped_tables > 0 and case_passed_tables == 0:
            banner("TEST CASE RESULT : SKIPPED")
            case_result_text = "SKIPPED"
            case_result_class = "chip-skip"
        else:
            banner("TEST CASE RESULT : PASSED")
            case_result_text = "PASSED"
            case_result_class = "chip-pass"

        html_report += f"""
<div class="case-footer">
  <span class="chip {case_result_class}">RESULT: {case_result_text}</span>
  <span class="chip chip-pass">PASSED TABLES: {case_passed_tables}</span>
  <span class="chip chip-fail">FAILED TABLES: {case_failed_tables}</span>
  <span class="chip chip-skip">SKIPPED TABLES: {case_skipped_tables}</span>
</div>
</div>
</details>
"""

    banner("EXECUTION SUMMARY")
    print(f"Total Test Cases : {total_cases}")
    print(f"Tables Checked  : {total_tables}")
    print(f"Tables Skipped  : {skipped_tables}")
    print(f"Tables Passed   : {passed_tables}")
    print(f"Tables Failed   : {failed_tables}")

    print("\nFAILURE SUMMARY")
    for f in failure_summary:
        print(" -", f)

    html_report += html_footer()

    os.makedirs("reports", exist_ok=True)
    with open("reports/idea1_report.html", "w", encoding="utf-8") as f:
        f.write(html_report)

    conn.close()

if __name__ == "__main__":
    main()

