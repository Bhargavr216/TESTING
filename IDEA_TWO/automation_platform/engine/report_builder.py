import os
import json
from datetime import datetime
from typing import List, Dict, Any
from .result_model import RuleResult

class ReportBuilder:
    def __init__(self, suite_name: str):
        self.suite_name = suite_name
        self.results: List[RuleResult] = []
        self.start_time = datetime.now()

    def add_results(self, scenario_results: List[RuleResult]):
        self.results.extend(scenario_results)

    def generate_reports(self):
        """
        Generates both console output and an HTML report.
        """
        self._print_console_summary()
        self._generate_html_report()

    def _print_console_summary(self):
        print("\n" + "="*80)
        print(f"SUITE EXECUTION SUMMARY: {self.suite_name}")
        print("="*80)
        
        passed = [r for r in self.results if r.status == 'PASS']
        failed = [r for r in self.results if r.status == 'FAIL']
        
        print(f"TOTAL RULES EXECUTED: {len(self.results)}")
        print(f"PASSED: {len(passed)}")
        print(f"FAILED: {len(failed)}")
        
        if failed:
            print("\n" + "-"*40)
            print("FAILURE DETAILS:")
            print("-"*40)
            for f in failed:
                print(f"SERVICE: {f.service} | SCENARIO: {f.scenario} | STATE: {f.state}")
                print(f"RULE: {f.rule_type} | TABLE: {f.table or 'N/A'} | COLUMN: {f.column or 'N/A'}")
                print(f"EXPECTED: {f.expected}")
                print(f"ACTUAL: {f.actual}")
                print(f"MESSAGE: {f.message}")
                print("-" * 20)
        
        print("\n" + "="*80)

    def _generate_html_report(self):
        """
        Generates a modern, scenario-centric HTML report with collapsible details.
        """
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(project_root, 'reports')
        
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            
        report_path = os.path.join(reports_dir, 'report.html')
        
        # Group results by scenario
        scenario_groups = {}
        for r in self.results:
            if r.scenario not in scenario_groups:
                scenario_groups[r.scenario] = {
                    'service': r.service,
                    'results': [],
                    'status': 'PASS'
                }
            scenario_groups[r.scenario]['results'].append(r)
            if r.status == 'FAIL':
                scenario_groups[r.scenario]['status'] = 'FAIL'

        # Summary Section
        passed_scenarios = len([s for s in scenario_groups.values() if s['status'] == 'PASS'])
        failed_scenarios = len([s for s in scenario_groups.values() if s['status'] == 'FAIL'])
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{self.suite_name} - Execution Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <style>
        :root {{ --pass-color: #28a745; --fail-color: #dc3545; --bg-light: #f4f7f9; }}
        body {{ background-color: var(--bg-light); font-family: 'Inter', system-ui, sans-serif; }}
        .navbar {{ background: #1a1c23; border-bottom: 3px solid #0d6efd; }}
        .summary-tile {{ background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 10px rgba(0,0,0,0.05); text-align: center; }}
        .scenario-card {{ border: none; border-radius: 12px; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; }}
        .scenario-header {{ cursor: pointer; padding: 1rem 1.5rem; display: flex; align-items: center; justify-content: space-between; transition: background 0.2s; }}
        .scenario-header:hover {{ background-color: #f8f9fa; }}
        .status-pill {{ padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem; }}
        .pill-pass {{ background: #d1e7dd; color: #0f5132; }}
        .pill-fail {{ background: #f8d7da; color: #842029; }}
        .rule-row {{ border-left: 4px solid #dee2e6; margin-left: 1rem; padding: 1rem; background: #fff; margin-bottom: 0.5rem; border-radius: 0 8px 8px 0; }}
        .rule-pass {{ border-left-color: var(--pass-color); }}
        .rule-fail {{ border-left-color: var(--fail-color); }}
        .json-block {{ background: #272822; color: #f8f8f2; padding: 1rem; border-radius: 6px; font-family: monospace; font-size: 0.85rem; overflow-x: auto; }}
        .log-line {{ font-family: 'Consolas', monospace; font-size: 0.85rem; color: #666; border-bottom: 1px solid #eee; padding: 2px 0; }}
        .filter-bar {{ background: white; padding: 1rem; border-radius: 12px; margin-bottom: 2rem; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-dark py-3 mb-4">
        <div class="container">
            <span class="navbar-brand mb-0 h1"><i class="bi bi-cpu"></i> Enterprise Validation Dashboard</span>
            <span class="text-light small"><i class="bi bi-calendar3"></i> {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}</span>
        </div>
    </nav>

    <div class="container">
        <!-- Summary Section -->
        <div class="row g-4 mb-4">
            <div class="col-md-3">
                <div class="summary-tile">
                    <h6 class="text-muted small fw-bold">TOTAL SCENARIOS</h6>
                    <h2 class="fw-bold mb-0">{len(scenario_groups)}</h2>
                </div>
            </div>
            <div class="col-md-3">
                <div class="summary-tile">
                    <h6 class="text-muted small fw-bold text-success">PASSED</h6>
                    <h2 class="fw-bold text-success mb-0">{passed_scenarios}</h2>
                </div>
            </div>
            <div class="col-md-3">
                <div class="summary-tile">
                    <h6 class="text-muted small fw-bold text-danger">FAILED</h6>
                    <h2 class="fw-bold text-danger mb-0">{failed_scenarios}</h2>
                </div>
            </div>
            <div class="col-md-3">
                <div class="summary-tile">
                    <h6 class="text-muted small fw-bold text-primary">RULES RUN</h6>
                    <h2 class="fw-bold text-primary mb-0">{len(self.results)}</h2>
                </div>
            </div>
        </div>

        <!-- Filter Bar -->
        <div class="filter-bar d-flex gap-3 align-items-center">
            <div class="flex-grow-1">
                <div class="input-group">
                    <span class="input-group-text bg-white border-end-0"><i class="bi bi-search"></i></span>
                    <input type="text" id="globalSearch" class="form-control border-start-0" placeholder="Search scenario or service..." onkeyup="filterScenarios()">
                </div>
            </div>
            <select id="serviceFilter" class="form-select w-auto" onchange="filterScenarios()">
                <option value="all">All Services</option>
                {"".join(f'<option value="{s}">{s}</option>' for s in sorted(list(set(r.service for r in self.results))))}
            </select>
        </div>

        <!-- Scenario List -->
        <div id="scenarioContainer">
        """
        
        for name, data in scenario_groups.items():
            status_class = "pill-pass" if data['status'] == 'PASS' else "pill-fail"
            status_icon = "bi-check-circle-fill text-success" if data['status'] == 'PASS' else "bi-x-circle-fill text-danger"
            
            html_content += f"""
            <div class="scenario-card bg-white" data-service="{data['service']}" data-name="{name}">
                <div class="scenario-header" onclick="toggleDetails('{name}')">
                    <div class="d-flex align-items-center gap-3">
                        <i class="bi {status_icon} fs-4"></i>
                        <div>
                            <div class="fw-bold text-dark">{name}</div>
                            <span class="badge bg-light text-muted border small">{data['service']}</span>
                        </div>
                    </div>
                    <div class="d-flex align-items-center gap-3">
                        <span class="status-pill {status_class}">{data['status']}</span>
                        <i class="bi bi-chevron-down" id="icon-{name}"></i>
                    </div>
                </div>
                
                <div class="collapse p-4 pt-0" id="details-{name}">
                    <hr class="mt-0">
                    <h6 class="fw-bold text-muted small mb-3 text-uppercase">Rule Validations</h6>
            """
            
            for r in data['results']:
                rule_status_class = "rule-pass" if r.status == 'PASS' else "rule-fail"
                rule_icon = "bi-check2 text-success" if r.status == 'PASS' else "bi-bug text-danger"
                
                html_content += f"""
                    <div class="rule-row {rule_status_class}">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="fw-bold small"><i class="bi {rule_icon} me-2"></i>{r.rule_type.upper()} Validation</span>
                            <span class="badge {'bg-success' if r.status == 'PASS' else 'bg-danger'}">{r.status}</span>
                        </div>
                        <div class="row g-2 small">
                            <div class="col-md-4"><strong>Table:</strong> {r.table or 'N/A'}</div>
                            <div class="col-md-4"><strong>Column:</strong> {r.column or 'N/A'}</div>
                            <div class="col-md-12 mt-3">
                                <div class="text-muted mb-1 text-uppercase small fw-bold">Validation Detail Table:</div>
                                <div class="table-responsive">
                                    <table class="table table-sm table-bordered mb-0 bg-white" style="font-size: 0.8rem;">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Table</th>
                                                <th>Field / Path</th>
                                                <th>Expected</th>
                                                <th>Actual</th>
                                                <th class="text-center">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {self._render_structured_logs(r.logs)}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                """
                
            html_content += """
                </div>
            </div>
            """
            
        html_content += """
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function toggleDetails(id) {
            const el = document.getElementById('details-' + id);
            const icon = document.getElementById('icon-' + id);
            const isVisible = el.classList.contains('show');
            
            if(isVisible) {
                new bootstrap.Collapse(el).hide();
                icon.classList.replace('bi-chevron-up', 'bi-chevron-down');
            } else {
                new bootstrap.Collapse(el).show();
                icon.classList.replace('bi-chevron-down', 'bi-chevron-up');
            }
        }

        function filterScenarios() {
            const search = document.getElementById('globalSearch').value.toLowerCase();
            const service = document.getElementById('serviceFilter').value;
            const cards = document.querySelectorAll('.scenario-card');

            cards.forEach(card => {
                const name = card.getAttribute('data-name').toLowerCase();
                const srv = card.getAttribute('data-service');
                const matchSearch = name.includes(search) || srv.toLowerCase().includes(search);
                const matchService = service === 'all' || srv === service;

                card.style.display = (matchSearch && matchService) ? 'block' : 'none';
            });
        }
    </script>
</body>
</html>
        """
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _format_value(self, val):
        if val is None: return "null"
        if isinstance(val, (dict, list)):
            try:
                from datetime import datetime
                from decimal import Decimal
                def handler(obj):
                    if isinstance(obj, datetime): return obj.isoformat()
                    if isinstance(obj, Decimal): return float(obj)
                    return str(obj)
                return json.dumps(val, indent=2, default=handler)
            except:
                return str(val)
        return str(val)

    def _format_logs(self, logs):
        return "".join(f'<div class="log-line">{line}</div>' for line in logs)

    def _render_structured_logs(self, logs):
        if not logs: return "<tr><td colspan='5' class='text-center'>No logs available</td></tr>"
        rows = ""
        for entry_str in logs:
            try:
                entry = json.loads(entry_str)
                status_class = "text-success" if entry['status'] == "PASS" else "text-danger fw-bold"
                rows += f"""
                <tr>
                    <td><code>{entry['table']}</code></td>
                    <td><code>{entry['path']}</code></td>
                    <td>{self._format_value(entry['expected'])}</td>
                    <td>{self._format_value(entry['actual'])}</td>
                    <td class="text-center {status_class}">{entry['status']}</td>
                </tr>
                """
            except:
                rows += f"<tr><td colspan='5'>{entry_str}</td></tr>"
        return rows
