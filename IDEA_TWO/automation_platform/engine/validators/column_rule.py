from typing import Dict, Any
from .base_rule import BaseRule
from ..result_model import RuleResult

class ColumnRule(BaseRule):
    def validate(self, **context) -> RuleResult:
        service = context.get('service')
        scenario = context.get('scenario')
        state = context.get('state')
        conn = context.get('conn')
        lookup_key = context.get('lookup_key')
        
        table = self.rule_config.get('table')
        conditions = self.rule_config.get('conditions', {})
        
        logs = [f"Starting column validation for table: {table}", f"Conditions: {conditions}"]
        
        columns = list(conditions.keys())
        query = f"SELECT {', '.join(columns)} FROM {table} WHERE event_id = %s"
        
        try:
            with conn.cursor() as cursor:
                logs.append(f"Executing query: {query}")
                cursor.execute(query, (lookup_key,))
                row = cursor.fetchone()
                
            if not row:
                logs.append("No record found for validation.")
                return RuleResult(status='FAIL', service=service, scenario=scenario, state=state, 
                                 rule_type='column', table=table, message="No record found", logs=logs)
            
            actual_values = dict(zip(columns, row))
            logs.append(f"Actual values retrieved: {actual_values}")
            failures = []
            
            for column, condition in conditions.items():
                actual_val = actual_values[column]
                for operator, expected_val in condition.items():
                    if not self._check_condition(actual_val, operator, expected_val):
                        err = f"{column}: expected {operator} {expected_val}, got {actual_val}"
                        failures.append(err)
                        logs.append(f"FAILURE: {err}")
                    else:
                        logs.append(f"SUCCESS: {column} {operator} {expected_val}")
            
            passed = len(failures) == 0
            return RuleResult(
                status='PASS' if passed else 'FAIL',
                service=service,
                scenario=scenario,
                state=state,
                rule_type='column',
                table=table,
                expected=conditions,
                actual=actual_values,
                message="; ".join(failures) if not passed else "Column validation passed",
                logs=logs
            )
        except Exception as e:
            logs.append(f"CRITICAL ERROR: {str(e)}")
            return RuleResult(status='FAIL', service=service, scenario=scenario, state=state, 
                             rule_type='column', table=table, message=str(e), logs=logs)

    def _check_condition(self, actual, operator, expected):
        if operator == 'equals':
            return actual == expected
        elif operator == 'not_equals':
            return actual != expected
        elif operator == 'greater_than':
            return actual > expected
        elif operator == 'less_than':
            return actual < expected
        elif operator == 'contains':
            return expected in str(actual)
        elif operator == 'in_list':
            return actual in expected
        return False
