from typing import Dict, Any
from .base_rule import BaseRule
from ..result_model import RuleResult

class RetryRule(BaseRule):
    def validate(self, **context) -> RuleResult:
        service = context.get('service')
        scenario = context.get('scenario')
        state = context.get('state')
        conn = context.get('conn')
        lookup_key = context.get('lookup_key')
        
        table = self.rule_config.get('table')
        expected_retry_count = self.rule_config.get('retry_count')
        expected_retry_state = self.rule_config.get('retry_state')
        
        logs = [f"Starting retry validation for table: {table}", f"Expected count: {expected_retry_count}, Expected state: {expected_retry_state}"]
        
        query = f"SELECT retry_count, state FROM {table} WHERE event_id = %s"
        
        try:
            with conn.cursor() as cursor:
                logs.append(f"Executing query: {query}")
                cursor.execute(query, (lookup_key,))
                row = cursor.fetchone()
                
            if not row:
                logs.append("No record found for retry validation.")
                return RuleResult(status='FAIL', service=service, scenario=scenario, state=state, 
                                 rule_type='retry', table=table, message="No record found", logs=logs)
            
            actual_retry_count, actual_retry_state = row
            logs.append(f"Actual - Retry count: {actual_retry_count}, State: {actual_retry_state}")
            failures = []
            
            if expected_retry_count is not None and actual_retry_count != expected_retry_count:
                err = f"retry_count: expected {expected_retry_count}, got {actual_retry_count}"
                failures.append(err)
                logs.append(f"FAILURE: {err}")
            
            if expected_retry_state is not None and actual_retry_state != expected_retry_state:
                err = f"retry_state: expected {expected_retry_state}, got {actual_retry_state}"
                failures.append(err)
                logs.append(f"FAILURE: {err}")
            
            passed = len(failures) == 0
            return RuleResult(
                status='PASS' if passed else 'FAIL',
                service=service,
                scenario=scenario,
                state=state,
                rule_type='retry',
                table=table,
                expected={'retry_count': expected_retry_count, 'state': expected_retry_state},
                actual={'retry_count': actual_retry_count, 'state': actual_retry_state},
                message="; ".join(failures) if not passed else "Retry validation passed",
                logs=logs
            )
        except Exception as e:
            logs.append(f"CRITICAL ERROR: {str(e)}")
            return RuleResult(status='FAIL', service=service, scenario=scenario, state=state, 
                             rule_type='retry', table=table, message=str(e), logs=logs)
