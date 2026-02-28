import json
from typing import Dict, Any, List
from .base_rule import BaseRule
from ..result_model import RuleResult

class AuditRule(BaseRule):
    def validate(self, **context) -> RuleResult:
        service = context.get('service')
        scenario = context.get('scenario')
        state = context.get('state')
        conn = context.get('conn')
        default_lookup = context.get('lookup_key')
        resolved_lookups = context.get('resolved_lookups', {})
        schema = context.get('schema', 'public')
        
        # Determine table name based on service and schema
        base_table = f"{service.lower()}_audit"
        table_name = f"{schema}.{base_table}" if schema != 'public' else base_table
        
        validations = self.rule_config.get('validations', {})
        
        # Use event_id from resolved lookups if available, else default
        event_id = resolved_lookups.get('event_id', default_lookup)
        
        structured_logs = []
        all_passed = True
        total_failures = []

        # 1. Fetch and Sort Audit Rows
        param_placeholder = '?' if hasattr(conn, 'getinfo') else '%s'
        query = f"SELECT operation, exception, event_time FROM {table_name} WHERE event_id = {param_placeholder} ORDER BY event_time ASC"
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (event_id,))
                rows = cursor.fetchall()
                actual_audit = []
                for r in rows:
                    actual_audit.append({
                        "operation": r[0],
                        "exception": r[1],
                        "event_time": r[2].isoformat() if r[2] else None
                    })

            # 2. Count Validation
            expected_count = validations.get('count')
            if expected_count is not None:
                match = len(actual_audit) == expected_count
                structured_logs.append({
                    "table": table_name,
                    "path": "AUDIT_COUNT",
                    "expected": expected_count,
                    "actual": len(actual_audit),
                    "status": "PASS" if match else "FAIL"
                })
                if not match:
                    all_passed = False
                    total_failures.append(f"Audit count mismatch: expected {expected_count}, got {len(actual_audit)}")

            # 3. Retry Attempts Validation
            expected_retries = validations.get('retry_attempts')
            if expected_retries is not None:
                # Count "VALIDATE" operations with exceptions
                retry_found = len([r for r in actual_audit if r['operation'] == 'VALIDATE' and r['exception'] is not None])
                match = retry_found == expected_retries
                structured_logs.append({
                    "table": table_name,
                    "path": "RETRY_ATTEMPTS",
                    "expected": expected_retries,
                    "actual": retry_found,
                    "status": "PASS" if match else "FAIL"
                })
                if not match:
                    all_passed = False
                    total_failures.append(f"Retry attempts mismatch: expected {expected_retries}, got {retry_found}")

            # 4. Sequence Validation
            expected_sequence = validations.get('exact_sequence')
            if expected_sequence:
                for i, exp_step in enumerate(expected_sequence):
                    if i >= len(actual_audit):
                        structured_logs.append({
                            "table": table_name,
                            "path": f"SEQUENCE_STEP_{i+1}",
                            "expected": exp_step,
                            "actual": "MISSING",
                            "status": "FAIL"
                        })
                        all_passed = False
                        total_failures.append(f"Missing sequence step {i+1}")
                        continue
                    
                    act_step = actual_audit[i]
                    # Validate operation
                    op_match = act_step['operation'] == exp_step['operation']
                    
                    # Validate exception
                    exp_exc = exp_step.get('exception')
                    act_exc = act_step['exception']
                    
                    exc_match = False
                    if exp_exc == "!MANDATORY":
                        exc_match = act_exc is not None
                    else:
                        exc_match = act_exc == exp_exc
                    
                    step_passed = op_match and exc_match
                    structured_logs.append({
                        "table": table_name,
                        "path": f"SEQUENCE_STEP_{i+1} ({exp_step['operation']})",
                        "expected": exp_step,
                        "actual": {"operation": act_step['operation'], "exception": act_step['exception']},
                        "status": "PASS" if step_passed else "FAIL"
                    })
                    if not step_passed:
                        all_passed = False
                        total_failures.append(f"Sequence mismatch at step {i+1}")

                # Check for extra steps
                if len(actual_audit) > len(expected_sequence):
                    all_passed = False
                    total_failures.append(f"Extra audit steps found: expected {len(expected_sequence)}, got {len(actual_audit)}")

        except Exception as e:
            all_passed = False
            structured_logs.append({"table": table_name, "path": "ERROR", "expected": "N/A", "actual": str(e), "status": "FAIL"})

        return RuleResult(
            status='PASS' if all_passed else 'FAIL',
            service=service,
            scenario=scenario,
            state=state,
            rule_type='audit_validate',
            message="; ".join(total_failures) if total_failures else "Audit validation passed.",
            logs=[json.dumps(log) for log in structured_logs]
        )
